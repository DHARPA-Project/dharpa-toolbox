# -*- coding: utf-8 -*-
import inspect
from inspect import Parameter, Signature
from typing import Type

import yaml
from dharpa_toolbox.modules.core import DharpaModule
from dharpa_toolbox.modules.utils import find_all_module_classes
from dharpa_toolbox.modules.workflows import DharpaWorkflow
from dharpa_toolbox.types.utils import (
    get_input_model_for_pydantic,
    get_output_model_for_pydantic,
)
from fastapi import APIRouter
from makefun import with_signature
from pydantic import BaseModel


def create_processing_functions(cls: Type):

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


def create_routers_from_modules() -> APIRouter:

    all_modules = {}

    module_router = APIRouter()
    workflow_router = APIRouter()

    all_classes = find_all_module_classes()

    for name in sorted(all_classes):

        cls = all_classes[name]

        if name == "dharpa_workflow":
            continue

        func, resp_model = create_processing_functions(cls)
        all_modules[name] = func

        is_workflow = True if issubclass(cls, DharpaWorkflow) else False
        if is_workflow:
            workflow_router.post(f"/{name}", response_model=resp_model)(func)
        else:
            module_router.post(f"/{name}", response_model=resp_model)(func)
        # router.get(f"/{t}s/{name}/doc")(describe_func)

    return module_router, workflow_router
