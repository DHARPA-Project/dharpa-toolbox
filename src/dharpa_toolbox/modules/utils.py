# -*- coding: utf-8 -*-
import os
import typing
from pathlib import Path
from typing import Any, Dict, Type, Union

from dharpa_toolbox.modules.core import DharpaModule
from dharpa_toolbox.utils import (
    get_data_from_file,
    get_snake_case_from_class,
    get_subclass_map,
    to_camel_case,
)
from rich.jupyter import print as rich_print


_AUTO_MODULE_ID: typing.Dict[typing.Type, int] = {}

VALID_WORKFLOW_FILE_EXTENSIONS = ["yaml", "yml", "json"]


def get_auto_module_id(module_cls: typing.Type, use_incremental_ids: bool = False):

    if not use_incremental_ids:
        return get_module_name_from_class(module_cls)

    nr = _AUTO_MODULE_ID.setdefault(module_cls, 0)
    _AUTO_MODULE_ID[module_cls] = nr + 1

    name = get_module_name_from_class(module_cls)

    return f"{name}_{nr}"


def find_all_module_classes():
    modules_to_load = [
        "dharpa_toolbox.modules.core",
        "dharpa_toolbox.modules.files",
        "dharpa_toolbox.modules.text",
    ]

    all_module_clases = get_subclass_map(
        DharpaModule,
        preload_modules=modules_to_load,
        key_func=get_module_name_from_class,
        override_duplicate_class=True,
    )
    return all_module_clases


def create_module(module: Union[str, Type]) -> DharpaModule:

    if isinstance(module, str):
        module_cls = find_all_module_classes().get(module, None)
        if module_cls is None:
            raise ValueError(f"No module type '{module}' available.")
    elif isinstance(module, type):
        module_cls = module
        if not issubclass(module_cls, DharpaModule):
            raise ValueError(f"Not a subclass of 'DharpaModule': {module}")
    else:
        module_cls = module.__class__

    module_obj = module_cls()

    return module_obj


def generate_workflow_class_from_file(path: Union[str, Path]):

    from dharpa_toolbox.modules.workflows import DharpaWorkflow

    if isinstance(path, str):
        path = Path(os.path.expanduser(path))

    file_name_without_ext = path.name.split(".")[0]
    content = get_data_from_file(path)

    doc = content.pop("_doc", None)

    def constructor(self, **config):
        config.update(content)
        DharpaWorkflow.__init__(self, **config)

    attrs = {
        "_module_name": file_name_without_ext,
        "__init__": constructor,
        "_workflow_config": content,
        "__doc__": doc,
    }

    cls = type(
        f"Workflow{to_camel_case(file_name_without_ext, capitalize=True)}",
        (DharpaWorkflow,),
        attrs,
    )

    return cls


def load_workflows(path: Union[str, Path]):

    if isinstance(path, str):
        path = Path(os.path.expanduser(path))

    result = {}

    for f in path.iterdir():

        if f.is_file() and any(
            f.name.endswith(ext) for ext in VALID_WORKFLOW_FILE_EXTENSIONS
        ):
            cls = generate_workflow_class_from_file(f)
            result[cls._module_name] = cls

    for k, v in result.items():
        globals()[k] = v

    return result


def list_available_module_names() -> typing.Iterable[str]:

    names = find_all_module_classes().keys()
    return list(sorted(names))


def describe_module(
    module: Union[str, DharpaModule, Type], wrap_in_type_name: bool = True
) -> Dict[str, Any]:

    if isinstance(module, str):
        module_cls = find_all_module_classes().get(module, None)
        if module_cls is None:
            raise ValueError(f"No module type '{module}' available.")
        module = module_cls()
    elif isinstance(module, type):
        module_cls = module
        if not issubclass(module_cls, DharpaModule):
            raise ValueError(f"Not a subclass of 'DharpaModule': {module}")
        module = module_cls()
    else:
        module_cls = module.__class__

    if not isinstance(module, DharpaModule) and not issubclass(
        module.__class__, DharpaModule
    ):
        raise ValueError(f"Object not a subclass of 'DharpaModule': {module}")

    result: Dict[str, Dict[str, Any]] = {"inputs": {}, "outputs": {}}
    for inp in module.input_names:
        inp_loc = module.get_input_location(inp)
        result["inputs"][inp] = inp_loc.value_type.__name__
    for out in module.output_names:
        out_loc = module.get_output_location(out)
        result["outputs"][out] = out_loc.value_type.__name__

    if not wrap_in_type_name:
        return result
    else:

        return {get_module_name_from_class(module_cls): result}


def print_module_desc(*module: Union[str, DharpaModule, Type]) -> None:

    result = {}

    if not module:
        module = list_available_module_names()  # type: ignore

    for m in module:
        result.update(describe_module(m))

    rich_print(result)


def get_module_name_from_class(cls: Type):

    if hasattr(cls, "_module_name"):
        return cls._module_name
    else:
        return get_snake_case_from_class(cls)
