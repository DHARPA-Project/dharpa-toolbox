# -*- coding: utf-8 -*-
import typing

import traitlets
from dharpa_toolbox.modules.core import DharpaModule
from pydantic import BaseModel, create_model


TYPEHINT_TRAITLET_MAP = {
    traitlets.Dict: typing.Dict,
    traitlets.Bool: bool,
    traitlets.Any: typing.Any,
    traitlets.List: typing.List,
}


def ensure_type_type(t):
    if isinstance(t, traitlets.TraitType):
        t = t.__class__
    return t


def get_python_type(t):

    t = ensure_type_type(t)
    return TYPEHINT_TRAITLET_MAP[t]


def convert_to_base_model(cls_name: str, traitlet: traitlets.HasTraits) -> BaseModel:

    fields = {}
    for trait_name, trait in traitlet.traits().items():

        converted_type = get_python_type(trait)
        fields[trait_name] = (converted_type, ...)

    base_model_cls = create_model(cls_name, **fields)
    return base_model_cls


def get_input_model_for_pydantic(module: DharpaModule):

    cls_name = f"{module.__class__.__name__}Input"
    model = convert_to_base_model(cls_name, module._state.inputs)
    return model


def get_output_model_for_pydantic(module: DharpaModule):

    cls_name = f"{module.__class__.__name__}Output"
    model = convert_to_base_model(cls_name, module._state.outputs)
    return model


def get_input_python_types(module: DharpaModule):

    result = {}

    for inp in module.input_names:
        inp_loc = module.get_input_location(inp)
        result[inp] = inp_loc.value_type

    return result
