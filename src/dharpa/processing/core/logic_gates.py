# -*- coding: utf-8 -*-
import time
import typing

from dharpa.data.core import DataSchema, DataType
from dharpa.models import ProcessingModuleConfig
from dharpa.processing.processing_module import ProcessingModule
from dharpa.workflows.modules import InputItems, OutputItems


class LogicProcessingModuleConfig(ProcessingModuleConfig):

    delay: float = 2


class LogicProcessingModule(ProcessingModule):

    _processing_step_config_cls = LogicProcessingModuleConfig


class NotProcessingModule(LogicProcessingModule):
    """Negates the input."""

    _module_name = "not"

    def _create_input_schema(self) -> typing.Mapping[str, DataSchema]:

        return {
            "a": DataSchema(DataType.boolean),
        }

    def _create_output_schema(self) -> typing.Mapping[str, DataSchema]:

        return {"y": DataSchema(DataType.boolean)}

    async def _process(self, inputs: InputItems, outputs: OutputItems) -> None:

        time.sleep(self.config.get("delay"))  # type: ignore

        outputs.y = not inputs.a


class AndProcessingModule(LogicProcessingModule):
    """Returns 'True' if both inputs are 'True'."""

    _module_name = "and"

    def _create_input_schema(self) -> typing.Mapping[str, DataSchema]:

        return {"a": DataSchema(DataType.boolean), "b": DataSchema(DataType.boolean)}

    def _create_output_schema(self) -> typing.Mapping[str, DataSchema]:

        return {"y": DataSchema(DataType.boolean)}

    async def _process(self, inputs: InputItems, outputs: OutputItems) -> None:

        time.sleep(self.config.get("delay"))  # type: ignore
        outputs.y = inputs.a and inputs.b


class OrProcessingModule(LogicProcessingModule):
    """Returns 'True' if one of the inputs is 'True'."""

    _module_name = "or"

    def _create_input_schema(self) -> typing.Mapping[str, DataSchema]:

        return {"a": DataSchema(DataType.boolean), "b": DataSchema(DataType.boolean)}

    def _create_output_schema(self) -> typing.Mapping[str, DataSchema]:

        return {"y": DataSchema(DataType.boolean)}

    async def _process(self, inputs: InputItems, outputs: OutputItems) -> None:

        time.sleep(self.config.get("delay"))  # type: ignore
        outputs.y = inputs.a or inputs.b
