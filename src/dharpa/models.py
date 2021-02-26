# -*- coding: utf-8 -*-
import typing

from dharpa import DHARPA_MODULES
from dharpa.defaults import MODULE_TYPE_KEY
from pydantic import BaseModel, root_validator, validator


if typing.TYPE_CHECKING:
    from dharpa.processing.processing_module import ProcessingModule
    from dharpa.workflows.workflow import DharpaWorkflow


class WorkflowModuleModel(BaseModel):
    """A class to hold data that describes a workflow."""

    modules: typing.List[typing.Mapping[str, typing.Any]]
    input_aliases: typing.Mapping[str, str] = {}
    output_aliases: typing.Mapping[str, str] = {}
    module_type_name: typing.Optional[str] = None
    doc: str = "-- n/a --"

    @validator("modules")
    def ensure_modules_format(cls, v):
        # TODO: clean up
        from dharpa.workflows.utils import create_workflow_modules

        create_workflow_modules(*v)
        return v

    def create_workflow(self, alias: str = None) -> "DharpaWorkflow":

        config = {
            "modules": self.modules,
            "input_aliases": self.input_aliases,
            "output_aliases": self.output_aliases,
        }
        proc_config = {MODULE_TYPE_KEY: "workflow", "config": config}

        from dharpa.workflows.workflow import DharpaWorkflow

        wf = DharpaWorkflow(alias=alias, processing_config=proc_config, doc=self.doc)
        return wf


class ProcessingModuleConfig(BaseModel):
    """Base class that describes the configuration a ProcessingModule class accepts.

    This is stored in the `_processing_step_config_cls` attribute in each ProcessingModule class. By default,
    such a ProcessingModule is not configurable.
    """

    pass


class WorkflowProcessingModuleConfig(ProcessingModuleConfig):
    """Default configuration class that describes the configuration for a WorkflowProcessingModule class."""

    modules: typing.List[typing.Mapping]
    input_aliases: typing.Mapping[str, str] = {}
    output_aliases: typing.Mapping[str, str] = {}

    class Config:
        arbitrary_types_allowed = True

    @validator("modules")
    def ensure_modules_format(cls, v):
        # TODO: clean up
        from dharpa.workflows.utils import create_workflow_modules

        create_workflow_modules(*v)
        return v


class WorkflowProcessingModuleConfigDynamic(ProcessingModuleConfig):
    """Default configuration class that describes the configuration for a subclass of WorkflowProcessingModule.

    The only difference is that the 'modules' key is optional. This is due to a minor implementation detail on how
    the classes are constructed dynamically, and should not matter in practice.
    """

    modules: typing.Optional[typing.List[typing.Mapping]] = None
    input_aliases: typing.Mapping[str, str] = {}
    output_aliases: typing.Mapping[str, str] = {}

    class Config:
        arbitrary_types_allowed = True

    @validator("modules")
    def ensure_modules_format(cls, v):
        from dharpa.workflows.utils import create_workflow_modules

        create_workflow_modules(*v)
        return v


class ProcessingConfig(BaseModel):
    @classmethod
    def from_dict(cls, **data: typing.Any):

        module_name = data.get(MODULE_TYPE_KEY, None)
        if module_name is None:
            raise ValueError(f"No '{MODULE_TYPE_KEY}' provided: {data}")

        config = data.get("config", {})
        return ProcessingConfig(module_type=module_name, config=config)

    module_type: str
    config: typing.Mapping[str, typing.Any] = {}

    @property
    def is_workflow(self) -> bool:
        return (
            DHARPA_MODULES.get_workflow(self.module_type, raise_exception=False)
            is not None
        )

    @root_validator(pre=True)
    def ensure_module_exists(cls, values):

        v = values.get(MODULE_TYPE_KEY, None)
        if v is None:
            raise ValueError(f"No '{MODULE_TYPE_KEY}' key specifified: {values}")

        processing_cls = DHARPA_MODULES.get(v, None)

        if processing_cls is None:
            raise ValueError(
                f"Can't parse config, module type '{v}' not loaded. Available modules: {', '.join(DHARPA_MODULES.module_names)}."
            )

        return values

    @validator("config")
    def ensure_config_valid(cls, v, values):

        module_type = values.get(MODULE_TYPE_KEY, None)
        if module_type is None:
            raise ValueError(f"No '{MODULE_TYPE_KEY}' key specifified: {values}")

        processing_cls = DHARPA_MODULES.get(module_type, None)
        if module_type is None:
            raise ValueError(f"No module with name '{module_type}' available.")
        config_model: typing.Type[
            ProcessingModuleConfig
        ] = processing_cls._processing_step_config_cls
        m = config_model(**v)

        return m.dict()

    def create_processing_module(self) -> "ProcessingModule":

        processing_cls: typing.Type[ProcessingModule] = DHARPA_MODULES.get(self.module_type, True)  # type: ignore
        return processing_cls(**self.config)
