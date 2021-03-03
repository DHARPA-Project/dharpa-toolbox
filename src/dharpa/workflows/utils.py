# -*- coding: utf-8 -*-
import os
import typing
from pathlib import Path
from typing import Type, Union

from dharpa.defaults import (
    DEFAULT_EXCLUDE_DIRS,
    DEFAULT_MODULES_TO_LOAD,
    MODULE_TYPE_NAME_KEY,
    VALID_WORKFLOW_FILE_EXTENSIONS,
)
from dharpa.models import ProcessingConfig
from dharpa.utils import (
    get_data_from_file,
    get_snake_case_from_class,
    get_subclass_map,
    to_camel_case,
)

if typing.TYPE_CHECKING:
    from dharpa.processing.processing_module import ProcessingModule
    from dharpa.workflows.modules import WorkflowModule
    from dharpa.workflows.workflow import WorkflowProcessingModule


def get_module_name_from_class(cls: Type):

    if hasattr(cls, "_module_name"):
        return cls._module_name
    else:
        return get_snake_case_from_class(cls)


def find_all_processing_module_classes(
    *modules_to_load: str,
) -> typing.Mapping[str, Type["ProcessingModule"]]:

    from dharpa.processing.processing_module import ProcessingModule
    from dharpa.workflows import workflow  # noqa

    if not modules_to_load:
        modules_to_load = DEFAULT_MODULES_TO_LOAD

    all_module_clases = get_subclass_map(
        ProcessingModule,
        preload_modules=modules_to_load,
        key_func=get_module_name_from_class,
        override_duplicate_class=True,
    )
    return all_module_clases


def find_workflow_descriptions(
    path: Union[str, Path], exclude_dirs: typing.Iterable[str] = DEFAULT_EXCLUDE_DIRS
) -> typing.Dict[str, typing.Mapping[str, typing.Any]]:

    if isinstance(path, str):
        path = Path(os.path.expanduser(path))

    result: typing.Dict[str, typing.Mapping[str, typing.Any]] = {}
    for root, dirnames, filenames in os.walk(path, topdown=True):

        if exclude_dirs:
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

        for filename in [
            f
            for f in filenames
            if os.path.isfile(os.path.join(root, f))
            and any(f.endswith(ext) for ext in VALID_WORKFLOW_FILE_EXTENSIONS)
        ]:

            path = os.path.join(root, filename)
            data = get_data_from_file(path)

            name = data.get(MODULE_TYPE_NAME_KEY, None)
            if name is None:
                name = filename.split(".", maxsplit=1)[0]

            if name in result.keys():
                raise Exception(f"Duplicate workflow name: {name}")
            result[name] = {"data": data, "path": path}

    return result


def generate_workflow_processing_class_from_config(
    module_name: str, config: "ProcessingConfig"
) -> typing.Type["WorkflowProcessingModule"]:

    _workflow_config = config.dict()["module_config"]

    def init(self, **m_config: typing.Any):
        m_config.update(_workflow_config)
        m_config.setdefault("meta", {}).update(config.meta)

        if not m_config.get("workflow_id", None):
            m_config["workflow_id"] = config.module_type

        super(self.__class__, self).__init__(**m_config)

    from dharpa.models import WorkflowProcessingModuleConfigDynamic
    from dharpa.workflows.workflow import WorkflowProcessingModule

    attrs = {
        "__init__": init,
        "_processing_step_config_cls": WorkflowProcessingModuleConfigDynamic,
        "_module_name": module_name,
    }
    d = config.meta.get("doc", None)
    if d:
        attrs["__doc__"] = d

    cls = type(
        f"Workflow{to_camel_case(module_name, capitalize=True)}",
        (WorkflowProcessingModule,),
        attrs,
    )
    return cls


# def create_workflow(module_name: str)


def create_workflow_modules(
    *configs: typing.Union["WorkflowModule", typing.Mapping],
    workflow_id: str = None,
    force_mappings: bool = True,
) -> typing.List["WorkflowModule"]:

    from dharpa.models import ProcessingConfig
    from dharpa.workflows.modules import WorkflowModule
    from dharpa.workflows.workflow import DharpaWorkflow

    result = []
    module_ids: typing.Set[str] = set()

    for c in configs:

        if isinstance(c, WorkflowModule):
            if force_mappings:
                raise TypeError(
                    "Using WorkflowModule classes not allowed in config (in this case)."
                )
            if c.workflow_id != workflow_id:
                raise ValueError(
                    f"Invalid workflow id '{c.workflow_id}' for module '{c.alias}': must match '{workflow_id}'"
                )
            m = c
        elif isinstance(c, typing.Mapping):

            _c = dict(c)
            m_id = _c.pop("module_alias", None)
            input_links = _c.pop("input_links", None)
            processing_config = ProcessingConfig.from_dict(**_c)

            if processing_config.is_pipeline:
                m = DharpaWorkflow(
                    alias=m_id,
                    workflow_id=workflow_id,
                    processing_config=processing_config,
                    input_links=input_links,
                )
            else:
                m = WorkflowModule(
                    alias=m_id,
                    workflow_id=workflow_id,
                    processing_config=processing_config,
                    input_links=input_links,
                )
            # m = WorkflowModule.from_dict(**c)
        else:
            raise TypeError(
                f"Can't create workflow modules, invalid type for module: '{type(c)}'"
            )

        if m.alias in module_ids:
            raise ValueError(
                f"Can't parse module configs: duplicate module ids: {m.alias}"
            )
        module_ids.add(m.alias)
        result.append(m)

    return result


_AUTO_MODULE_ID: typing.Dict[str, int] = {}


def get_auto_module_alias(
    module_cls: typing.Union[typing.Type, str], use_incremental_ids: bool = False
) -> str:
    """Return an id for a module obj of a provided module class.

    If 'use_incremental_ids' is set to True, a unique id is returned.

    Args:
        module_cls (Type): the module class (inherits from DharpaModule)
        use_incremental_ids (bool): whether to return a unique (incremental) id

    Returns:
        str: a module id
    """

    if isinstance(module_cls, str):
        name = module_cls
    else:
        name = get_module_name_from_class(module_cls)
    if not use_incremental_ids:
        return name

    nr = _AUTO_MODULE_ID.setdefault(name, 0)
    _AUTO_MODULE_ID[name] = nr + 1

    return f"{name}_{nr}"
