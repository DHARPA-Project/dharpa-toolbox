# -*- coding: utf-8 -*-
import inspect
from inspect import Parameter, Signature
from typing import Dict, Iterable, List, Optional, Tuple, Type

import yaml
from dharpa_toolbox.modules.core import DharpaModule
from dharpa_toolbox.modules.utils import describe_module, find_all_module_classes
from dharpa_toolbox.modules.workflows import DharpaWorkflow
from dharpa_toolbox.types.utils import (
    get_input_model_for_pydantic,
    get_output_model_for_pydantic,
)
from fastapi import APIRouter
from makefun import with_signature
from pydantic import BaseModel


def create_processing_function(cls: Type):

    obj: DharpaModule = cls()
    model: BaseModel = get_input_model_for_pydantic(obj)

    resp_model: BaseModel = get_output_model_for_pydantic(obj)

    parameters = [
        Parameter("item", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=model)
    ]
    sig = Signature(parameters)

    @with_signature(sig, func_name=obj.id)
    async def func(item: model):

        _obj: DharpaModule = cls()

        inp = {}
        for k in item.__fields__.keys():
            v = getattr(item, k)
            inp[k] = v

            _obj.set_input(k, v)

        result = {}

        _obj.process()

        for k in _obj.output_names:
            result[k] = _obj.get_output(k)

        return result

    doc = obj.__doc__
    if not doc:
        doc = "-- no documentation available --"
    doc = inspect.cleandoc(doc)

    doc = f"**Description**\n\n{doc}\n"

    if isinstance(obj, DharpaWorkflow) or issubclass(obj.__class__, DharpaWorkflow):
        if hasattr(obj, "_workflow_config") and obj._workflow_config:  # type: ignore
            content = yaml.dump(obj._workflow_config)  # type: ignore
            doc = f"{doc}\n**Workflow config**\n\n```\n{content}\n```"

    func.__doc__ = doc

    return func, resp_model


class ModuleDocModel(BaseModel):

    doc: str
    spec: Dict
    is_workflow: bool
    workflow_config: Optional[Dict]


def create_documenting_function(cls: Type):

    obj: DharpaModule = cls()

    sig = Signature([])

    is_workflow = False
    content = None
    if isinstance(obj, DharpaWorkflow) or issubclass(obj.__class__, DharpaWorkflow):
        if hasattr(obj, "_workflow_config") and obj._workflow_config:  # type: ignore
            content = obj._workflow_config  # type: ignore
            is_workflow = True

    @with_signature(sig, func_name=obj.id)
    async def func():

        desc = describe_module(obj, wrap_in_type_name=False)

        doc = obj.__doc__
        if not doc:
            doc = "-- no documentation available --"
        doc = inspect.cleandoc(doc)

        result = {"doc": doc, "spec": desc, "is_workflow": is_workflow}
        if content:
            result["workflow_config"] = content

        return ModuleDocModel(**result)

    if is_workflow:
        t = "workflow"
    else:
        t = "module"

    func_doc = f"""Retrieve details for {t} '{obj.id}'"""
    func.__doc__ = func_doc

    return func


class ModuleIdModel(BaseModel):

    ids: List[str]


def create_doc_nav_router(
    all_names: Iterable[str], all_modules: Iterable[str], all_workflows: Iterable[str]
):

    router = APIRouter()

    async def all_ids():
        return ModuleIdModel(ids=all_names)

    async def all_module_ids():
        return ModuleIdModel(ids=all_modules)

    async def all_workflow_ids():
        return ModuleIdModel(ids=all_workflows)

    router.get("/", response_model=ModuleIdModel)(all_ids)
    router.get("/modules", response_model=ModuleIdModel)(all_module_ids)
    router.get("/workflows", response_model=ModuleIdModel)(all_workflow_ids)

    return router


def create_doc_routers_from_modules() -> Tuple[APIRouter, APIRouter, APIRouter]:

    module_router = APIRouter()
    workflow_router = APIRouter()

    all_classes = find_all_module_classes()

    all_names = []
    all_module_names = []
    all_workflow_names = []

    for name in sorted(all_classes):

        all_names.append(name)

        cls = all_classes[name]

        if name == "dharpa_workflow":
            continue

        func = create_documenting_function(cls)

        is_workflow = True if issubclass(cls, DharpaWorkflow) else False
        if is_workflow:
            all_workflow_names.append(name)
            workflow_router.get(f"/{name}", response_model=ModuleDocModel)(func)
        else:
            all_module_names.append(name)
            module_router.get(f"/{name}", response_model=ModuleDocModel)(func)

    nav_router = create_doc_nav_router(
        all_names=all_names,
        all_modules=all_module_names,
        all_workflows=all_workflow_names,
    )

    return nav_router, module_router, workflow_router


def create_processing_routers_from_modules() -> Tuple[APIRouter, APIRouter]:

    module_router = APIRouter()
    workflow_router = APIRouter()

    all_classes = find_all_module_classes()

    for name in sorted(all_classes):

        cls = all_classes[name]

        if name == "dharpa_workflow":
            continue

        func, resp_model = create_processing_function(cls)

        is_workflow = True if issubclass(cls, DharpaWorkflow) else False
        if is_workflow:
            workflow_router.post(f"/{name}", response_model=resp_model)(func)
        else:
            module_router.post(f"/{name}", response_model=resp_model)(func)

    return module_router, workflow_router
