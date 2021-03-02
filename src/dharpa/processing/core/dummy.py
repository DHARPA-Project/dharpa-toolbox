# -*- coding: utf-8 -*-
import time
import typing

from dharpa.data.core import DataSchema
from dharpa.models import ProcessingModuleConfig
from dharpa.workflows.modules import ProcessingModule
from pydantic import Field


if typing.TYPE_CHECKING:
    from dharpa.workflows.modules import InputItems, OutputItems


class DummyProcessingModuleConfig(ProcessingModuleConfig):
    """Configuration for the 'dummy' processing module."""

    input_schema: typing.Mapping[str, typing.Mapping] = Field(
        description="the input schema for this module"
    )
    output_schema: typing.Mapping[str, typing.Mapping] = Field(
        description="the output schema for this module"
    )
    # inputs: typing.Mapping[str, typing.Any] = Field(description="the (dummy) input for this module", default_factory=dict)
    outputs: typing.Mapping[str, typing.Any] = Field(
        description="the (dummy) output for this module", default_factory=dict
    )
    delay: float = Field(
        description="the delay in seconds from processing start to when the (dummy) outputs are returned",
        default=0,
    )


class DummyProcessingModule(ProcessingModule):
    """Module that simulates processing, but uses hard-coded outputs as a result."""

    _module_name = "dummy"

    _processing_step_config_cls = DummyProcessingModuleConfig

    def _create_input_schema(self) -> typing.Mapping[str, DataSchema]:
        result = {}
        for k, v in self.config.get("input_schema").items():  # type: ignore
            result[k] = DataSchema(**v)
        return result

    def _create_output_schema(self) -> typing.Mapping[str, DataSchema]:
        result = {}
        for k, v in self.config.get("output_schema").items():  # type: ignore
            result[k] = DataSchema(**v)
        return result

    async def _process(self, inputs: "InputItems", outputs: "OutputItems") -> None:

        time.sleep(self.config.get("delay"))  # type: ignore

        output_values: typing.Mapping = self.config.get("outputs")  # type: ignore
        outputs.set_values(**output_values)
