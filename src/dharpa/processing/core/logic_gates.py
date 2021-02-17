# -*- coding: utf-8 -*-
import typing

from dharpa.data.core import DataSchema, DataType
from dharpa.processing.processing_module import ProcessingModule
from dharpa.workflows.modules import InputItems, OutputItems


class NotProcessingModule(ProcessingModule):

    _module_name = "not"

    def _create_input_schema(self) -> typing.Mapping[str, DataSchema]:

        return {
            "a": DataSchema(DataType.boolean),
        }

    def _create_output_schema(self) -> typing.Mapping[str, DataSchema]:

        return {"y": DataSchema(DataType.boolean)}

    def _process(self, inputs: InputItems, outputs: OutputItems) -> None:

        outputs.y = not inputs.a


class AndProcessingModule(ProcessingModule):

    _module_name = "and"

    def _create_input_schema(self) -> typing.Mapping[str, DataSchema]:

        return {"a": DataSchema(DataType.boolean), "b": DataSchema(DataType.boolean)}

    def _create_output_schema(self) -> typing.Mapping[str, DataSchema]:

        return {"y": DataSchema(DataType.boolean)}

    def _process(self, inputs: InputItems, outputs: OutputItems) -> None:

        outputs.y = inputs.a and inputs.b


class OrProcessingModule(ProcessingModule):

    _module_name = "or"

    def _create_input_schema(self) -> typing.Mapping[str, DataSchema]:

        return {"a": DataSchema(DataType.boolean), "b": DataSchema(DataType.boolean)}

    def _create_output_schema(self) -> typing.Mapping[str, DataSchema]:

        return {"y": DataSchema(DataType.boolean)}

    def _process(self, inputs: InputItems, outputs: OutputItems) -> None:

        outputs.y = inputs.a or inputs.b
