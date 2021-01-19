# -*- coding: utf-8 -*-
from inspect import Parameter, Signature
from typing import Any, List, Type

import traitlets
import typer
from dharpa_toolbox.modules.core import DharpaModule
from dharpa_toolbox.modules.utils import find_all_module_classes
from dharpa_toolbox.types.utils import get_input_python_types
from fastapi import APIRouter
from makefun import with_signature
from typer import Typer


TRAITLETS_TYPER_INPUT_MAP = {
    traitlets.Any: (str, {"default": ...}),
    traitlets.Bool: (
        bool,
        {
            "default": ...,
        },
    ),
    traitlets.Dict: (List[str], {"default": ...}),
    traitlets.List: (List[str], {"default": ...}),
}


def create_processing_function_for_typer(cls: Type):

    obj: DharpaModule = cls()

    input_types = get_input_python_types(obj)

    parameters = []
    for k, v in input_types.items():

        typer_conf = TRAITLETS_TYPER_INPUT_MAP[v]
        opt = typer.Option(**typer_conf[1])

        p = Parameter(
            name=k, kind=Parameter.KEYWORD_ONLY, annotation=typer_conf[0], default=opt
        )
        parameters.append(p)

    signature = Signature(parameters=parameters)

    @with_signature(signature, func_name=obj.id)
    def func(**inputs: Any):

        _obj: DharpaModule = cls()

        for k, v in inputs.items():

            if _obj._state.inputs.traits().get(k).__class__ == traitlets.Dict:
                _v = {}
                for value in v:
                    tokens = value.split("=", maxsplit=1)
                    _v[tokens[0]] = tokens[1]
                v = _v

            else:
                try:
                    # TODO: improve this
                    v = _obj._state.inputs.traits().get(k).from_string(v)
                except Exception:
                    pass

            _obj.set_input(k, v)

        result = {}

        _obj.process()

        for k in _obj.output_names:
            result[k] = _obj.get_output(k)

        print(result)

        return result

    # async def describe_func():
    #
    #     _obj: DharpaModule = cls()
    #
    #     result = describe_module(_obj)
    #     return result

    return func


def create_typers_from_modules() -> APIRouter:

    typer = Typer()

    all_modules = {}

    all_classes = find_all_module_classes()

    for name in sorted(all_classes):

        cls = all_classes[name]

        if name == "dharpa_workflow":
            continue

        func = create_processing_function_for_typer(cls)
        all_modules[name] = func

        typer.command(name)(func)

    return typer
