# -*- coding: utf-8 -*-
import json
import os
import typing
from pathlib import Path

import yaml
from dharpa.data.core import DataItem, DataSchema
from dharpa.processing.processing_module import (
    ProcessingModule,
    ProcessingModuleConfig,
    get_auto_module_id,
)
from dharpa.workflows.modules import InputItems, OutputItems, State, WorkflowModule
from dharpa.workflows.structure import WorkflowStructure, parse_module_configs
from pydantic import validator


class WorkflowPorcessingModuleConfig(ProcessingModuleConfig):

    modules: typing.Iterable[WorkflowModule]
    workflow_inputs: typing.Mapping[str, str] = {}
    workflow_outputs: typing.Mapping[str, str] = {}

    class Config:
        arbitrary_types_allowed = True

    @validator("modules")
    def ensure_modules_format(cls, v):
        parsed = parse_module_configs(*v)
        return parsed


class AssembledWorkflow(object):
    def __init__(
        self, structure: WorkflowStructure, inputs: InputItems, outputs: OutputItems
    ):

        self._structure: WorkflowStructure = structure
        self._inputs: InputItems = inputs
        self._outputs: OutputItems = outputs

    @property
    def inputs(self) -> InputItems:
        return self._inputs

    @property
    def outputs(self) -> OutputItems:
        return self._outputs

    def process(self):

        for stage in self._structure.execution_stages:

            for m_id in stage:
                module = self._structure.get_module(m_id)

                if module.state == State.RESULTS_READY:
                    continue
                elif module.state == State.PROCESSING:
                    raise Exception("Processing currently")
                elif module.state == State.INPUTS_READY:
                    module.process()
                else:
                    # inputs not ready
                    continue


class WorkflowProcessingModule(ProcessingModule):

    _module_name = "workflow"

    def __init__(self, **config: typing.Any):

        super().__init__(**config)

        self._workflow_structure: WorkflowStructure = WorkflowStructure(
            *self._config.modules  # type: ignore
        )

    def _processing_step_config_cls(self) -> typing.Type[ProcessingModuleConfig]:
        return WorkflowPorcessingModuleConfig

    @property
    def structure(self) -> WorkflowStructure:
        return self._workflow_structure

    def _create_input_schema(self) -> typing.Mapping[str, DataSchema]:
        return {
            input_name: w_in.schema
            for input_name, w_in in self._workflow_structure.workflow_inputs.items()
        }

    def _create_output_schema(self) -> typing.Mapping[str, DataSchema]:
        return {
            output_name: w_out.schema
            for output_name, w_out in self._workflow_structure.workflow_outputs.items()
        }

    def create_assembled_workflow(
        self, workflow_inputs: InputItems
    ) -> AssembledWorkflow:

        structure = WorkflowStructure(*self._config.modules)  # type: ignore

        structure_inputs: InputItems = InputItems(**self.input_schemas)
        structure_outputs: OutputItems = OutputItems(**self.output_schemas)

        for module_id, module_details in structure.module_details.items():

            module_inputs = module_details["inputs"]
            module_obj: WorkflowModule = module_details["workflow_module"]

            for input_name, link in module_inputs.items():
                connected_item = link.connected_item
                input_item = module_obj.inputs[input_name]

                if connected_item.link_type == "workflow_input":
                    workflow_input: DataItem = structure_inputs[
                        connected_item.value_name
                    ]
                    workflow_input.add_callback(input_item.set_value)
                    outer_workflow_input: DataItem = workflow_inputs[
                        connected_item.value_name
                    ]
                    workflow_input.value = outer_workflow_input.value
                else:
                    module_id = connected_item.module_id
                    value_name = connected_item.value_name
                    other = structure.get_module(module_id)
                    output_item = other.outputs[value_name]
                    output_item.add_callback(input_item.set_value)

            module_outputs = module_details["outputs"]
            for output_name, link in module_outputs.items():
                output_item = module_obj.outputs[output_name]

                for wo in link.workflow_outputs:
                    wo_item = structure_outputs[wo.value_name]
                    output_item.add_callback(wo_item.set_value)

        return AssembledWorkflow(
            structure=structure, inputs=structure_inputs, outputs=structure_outputs
        )

    def _process(self, inputs: InputItems, outputs: OutputItems) -> None:

        workflow = self.create_assembled_workflow(inputs)
        workflow.process()

        for k, v in workflow.outputs.items():
            outputs[k].value = v.value


class DharpaWorkflow(WorkflowModule):
    @classmethod
    def from_file(cls, path: typing.Union[str, Path], id: typing.Optional[str] = None):
        """Create a workflow object from configuration stored in a yaml or json file."""

        if isinstance(path, str):
            path = Path(os.path.expanduser(path))

        content = path.read_text()

        if path.name.endswith(".json"):
            content_type = "json"
        elif path.name.endswith(".yaml") or path.name.endswith(".yml"):
            content_type = "yaml"
        else:
            raise ValueError(
                "Invalid file format, only 'json' and 'yaml' supported for now."
            )

        if content_type == "json":
            config = json.loads(content)
        else:
            config = yaml.safe_load(content)

        if not id:
            id = get_auto_module_id("workflow")

        return DharpaWorkflow(id=id, **config)

    def __init__(
        self,
        type: str = "workflow",
        id: str = None,
        input_links: typing.Mapping[str, typing.Any] = None,
        **config: typing.Any,
    ):

        super().__init__(type=type, id=id, input_links=input_links, **config)
        if not isinstance(self._processing_obj, WorkflowProcessingModule):
            raise TypeError(
                f"Invalid class for processing object in workflow: {self._processing_obj.__class__}"
            )

    @property
    def structure(self) -> WorkflowStructure:
        return self._processing_obj.stucture  # type: ignore

    def create_assembled_workflow(self) -> AssembledWorkflow:

        return self._processing_obj.create_assembled_workflow(self.inputs)  # type: ignore
