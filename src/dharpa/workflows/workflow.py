# -*- coding: utf-8 -*-
import json
import os
import typing
from pathlib import Path

import yaml
import zmq
from dharpa.data.core import DataItem, DataSchema
from dharpa.defaults import MODULE_TYPE_KEY
from dharpa.models import ProcessingConfig, ProcessingModuleConfig
from dharpa.processing.executors import Processor
from dharpa.processing.processing_module import ProcessingModule
from dharpa.workflows.events import ModuleEvent, ModuleEventType, State
from dharpa.workflows.modules import InputItems, OutputItems, WorkflowModule
from dharpa.workflows.structure import WorkflowStructure
from dharpa.workflows.utils import create_workflow_modules, get_auto_module_id
from pydantic import validator


class WorkflowProcessingModuleConfig(ProcessingModuleConfig):

    modules: typing.List[typing.Mapping]
    input_aliases: typing.Mapping[str, str] = {}
    output_aliases: typing.Mapping[str, str] = {}

    class Config:
        arbitrary_types_allowed = True

    @validator("modules")
    def ensure_modules_format(cls, v):
        create_workflow_modules(*v)
        return v


class WorkflowProcessingModuleConfigDynamic(ProcessingModuleConfig):

    modules: typing.Optional[typing.List[typing.Mapping]] = None
    input_aliases: typing.Mapping[str, str] = {}
    output_aliases: typing.Mapping[str, str] = {}

    class Config:
        arbitrary_types_allowed = True

    @validator("modules")
    def ensure_modules_format(cls, v):
        create_workflow_modules(*v)
        return v


class AssembledWorkflowInteractive(object):
    def __init__(
        self,
        *module_configs: typing.Mapping[str, typing.Any],
        workflow_id: str = None,
        init_inputs: typing.Optional[InputItems] = None,
    ):

        self._module_configs: typing.Iterable[
            typing.Mapping[str, typing.Any]
        ] = module_configs
        self._workflow_id: typing.Optional[str] = workflow_id
        self._structure: WorkflowStructure = None  # type: ignore
        # self._inputs: InputItems = inputs
        # self._outputs: OutputItems = outputs

        self._zmq_context: zmq.Context = zmq.Context.instance()
        self._module_event_socket: zmq.Socket = self._zmq_context.socket(zmq.PULL)
        self._module_event_socket.bind(f"inproc://{self._workflow_id}")
        self._module_event_socket.bind("tcp://127.0.0.1:5555")

        self._init_obj(init_inputs=init_inputs)

    def _init_obj(self, init_inputs: typing.Optional[InputItems]) -> None:

        m = create_workflow_modules(*self._module_configs)
        self._structure = WorkflowStructure(*m, workflow_id=self._workflow_id)

        structure_inputs: InputItems = InputItems(
            **self._structure.workflow_input_schema
        )
        structure_outputs: OutputItems = OutputItems(
            **self._structure.workflow_output_schema
        )

        for module_id, module_details in self._structure.module_details.items():

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
                    if init_inputs:
                        outer_workflow_input: DataItem = init_inputs[
                            connected_item.value_name
                        ]
                        workflow_input.value = outer_workflow_input.value
                else:
                    module_id = connected_item.module_id
                    value_name = connected_item.value_name
                    other = self._structure.get_module(module_id)
                    output_item = other.outputs[value_name]
                    output_item.add_callback(input_item.set_value)

            module_outputs = module_details["outputs"]
            for output_name, link in module_outputs.items():
                output_item = module_obj.outputs[output_name]

                for wo in link.workflow_outputs:
                    wo_item = structure_outputs[wo.value_name]
                    output_item.add_callback(wo_item.set_value)

        self._inputs = structure_inputs
        self._outputs = structure_outputs

        pass

    @property
    def inputs(self) -> InputItems:
        return self._inputs

    @property
    def outputs(self) -> OutputItems:
        return self._outputs

    def listen(self) -> None:

        try:
            while True:
                # print("wating")
                event_data = self._module_event_socket.recv_json()
                event = ModuleEvent.from_dict(**event_data)

                # print(f"NEW EVENT: {event.to_dict()}")

                if event.event_type == ModuleEventType.set_input:
                    module_id = event.event_obj.module_id
                    if module_id != self._workflow_id:
                        raise NotImplementedError()

                    input_name = event.event_obj.input_name
                    value = event.event_obj.value

                    self._set_input(input_name=input_name, value=value)

                else:
                    raise NotImplementedError()

                print("yyy")
        except Exception as e:
            print(e)

        print("EXIT")

    def _set_input(self, input_name: str, value: typing.Any):

        inp = self.inputs[input_name]
        inp.value = value


class AssembledWorkflowBatch(object):

    # def create(self, workflow: typing.Union["DharpaWorkflow", "WorkflowProcessingModule", typing.Iterable[typing.Mapping[str, typing.Any]]], init_inputs: typing.Optional[InputItems]=None, input_aliases: typing.Mapping[str, str]=None, output_aliases: typing.Mapping[str, str]=None):
    #
    #     if isinstance(workflow, DharpaWorkflow):
    #         workflow = workflow._procecessing_obj
    #
    #     if isinstance(workflow, WorkflowProcessingModule):
    #         workflow = workflow.config.modules
    #
    #     # here we have a list of dicts (module configs)
    #     return AssembledWorkflowBatch(*workflow, init_inputs=init_inputs, input_aliases=input_aliases, output_aliases=output_aliases)

    def __init__(
        self,
        *module_configs: typing.Mapping,
        workflow_id: typing.Optional[str],
        init_inputs: typing.Optional[InputItems] = None,
        input_aliases: typing.Mapping[str, str] = None,
        output_aliases: typing.Mapping[str, str] = None,
    ):

        self._module_configs: typing.Iterable[typing.Mapping] = module_configs
        self._workflow_id: typing.Optional[str] = workflow_id
        self._input_aliases: typing.Optional[typing.Mapping[str, str]] = input_aliases
        self._output_aliases: typing.Optional[typing.Mapping[str, str]] = output_aliases

        self._structure: WorkflowStructure = None  # type: ignore
        self._inputs: InputItems = None  # type: ignore
        self._outputs: OutputItems = None  # type: ignore

        self._init_obj(init_inputs=init_inputs)

    def _init_obj(self, init_inputs: typing.Optional[InputItems] = None):

        self._structure = WorkflowStructure(
            *self._module_configs,
            input_aliases=self._input_aliases,
            output_aliases=self._output_aliases,
            workflow_id=self._workflow_id,
        )

        structure_inputs: InputItems = InputItems(
            **self._structure.workflow_input_schema
        )
        structure_outputs: OutputItems = OutputItems(
            **self._structure.workflow_output_schema
        )

        for module_id, module_details in self._structure.module_details.items():

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
                    if init_inputs:
                        outer_workflow_input: DataItem = init_inputs[
                            connected_item.value_name
                        ]
                        workflow_input.value = outer_workflow_input.value
                else:
                    module_id = connected_item.module_id
                    value_name = connected_item.value_name
                    other = self._structure.get_module(module_id)
                    output_item = other.outputs[value_name]
                    output_item.add_callback(input_item.set_value)

            module_outputs = module_details["outputs"]
            for output_name, link in module_outputs.items():
                output_item = module_obj.outputs[output_name]

                for wo in link.workflow_outputs:
                    wo_item = structure_outputs[wo.value_name]
                    output_item.add_callback(wo_item.set_value)

        self._inputs = structure_inputs
        self._outputs = structure_outputs

    @property
    def inputs(self) -> InputItems:
        return self._inputs

    @property
    def outputs(self) -> OutputItems:
        return self._outputs

    async def process_workflow(self, executor: Processor = None):

        for stage in self._structure.execution_stages:

            staged = []
            for m_id in stage:
                module = self._structure.get_module(m_id)

                if module.state == State.RESULTS_READY:
                    continue
                elif module.state == State.RESULTS_INCOMING:
                    raise Exception("Processing currently")
                elif module.state == State.INPUTS_READY:
                    if executor is None:
                        await module.process()
                    else:
                        # pb = ProcessingBundle(processing_module=module._processing_obj, inputs=module.inputs, outputs=module.outputs)
                        staged.append(module)

                else:
                    # inputs not ready
                    continue

            if executor:
                await executor.process(*staged)


class WorkflowProcessingModule(ProcessingModule):

    _module_name = "workflow"
    _processing_step_config_cls: typing.Type[
        ProcessingModuleConfig
    ] = WorkflowProcessingModuleConfig

    def __init__(self, **config: typing.Any):

        self._config: WorkflowProcessingModuleConfig

        self._workflow_structure: typing.Optional[WorkflowStructure] = None
        self._workflow_id: typing.Optional[str] = None
        super().__init__(**config)

    def set_workflow_id(self, workflow_id: str):
        self._workflow_structure = None
        self._workflow_id = workflow_id

    @property
    def structure(self) -> WorkflowStructure:
        if self._workflow_structure is None:
            self._workflow_structure = WorkflowStructure(
                *self._config.modules,  # type: ignore
                input_aliases=self._config.input_aliases,
                output_aliases=self._config.output_aliases,
                workflow_id=self._workflow_id,
            )
        return self._workflow_structure

    def _create_input_schema(self) -> typing.Mapping[str, DataSchema]:
        return self.structure.workflow_input_schema

    def _create_output_schema(self) -> typing.Mapping[str, DataSchema]:
        return self.structure.workflow_output_schema

    async def _process(
        self, inputs: InputItems, outputs: OutputItems, workflow_id: str = None
    ) -> None:

        workflow = AssembledWorkflowBatch(
            *self._config.modules,
            workflow_id=workflow_id,
            init_inputs=inputs,
            input_aliases=self._config.input_aliases,
            output_aliases=self._config.output_aliases,
        )
        await workflow.process_workflow()

        for k, v in workflow.outputs.items():
            outputs[k].value = v.value

    async def _process_workflow(
        self,
        inputs: InputItems,
        outputs: OutputItems,
        workflow_id: str = None,
        executor: Processor = None,
    ) -> None:

        workflow = AssembledWorkflowBatch(
            *self._config.modules,
            workflow_id=workflow_id,
            init_inputs=inputs,
            input_aliases=self._config.input_aliases,
            output_aliases=self._config.output_aliases,
        )
        await workflow.process_workflow(executor=executor)

        for k, v in workflow.outputs.items():
            outputs[k].value = v.value

    def _get_doc(self) -> str:

        result = "Steps:"

        for i, stage in enumerate(self.structure.execution_stages):
            result = f"{result}\n\nStage {i}:\n"
            for m_id in stage:
                m = self.structure.get_module(m_id)
                result = f"{result}\n\t{m.id}: {m.doc}"

        return result


class DharpaWorkflow(WorkflowModule):
    @classmethod
    def from_file(
        cls,
        path: typing.Union[str, Path],
        module_type_name: typing.Optional[str] = None,
    ):
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

        config_module_type_name = config.pop(MODULE_TYPE_KEY + "_name", None)
        if not module_type_name:
            if config_module_type_name:
                module_type_name = get_auto_module_id(config_module_type_name)
            else:
                file_name_without_ext = path.name.split(".", maxsplit=1)[0]
                module_type_name = get_auto_module_id(file_name_without_ext)

        input_links = config.pop("input_links", None)
        doc = config.pop("doc", None)

        return DharpaWorkflow(
            id=module_type_name,
            processing_config={"module_name": "workflow", "config": config},
            input_links=input_links,
            doc=doc,
        )

    def __init__(
        self,
        processing_config: typing.Union[
            ProcessingConfig, typing.Mapping[str, typing.Any]
        ],
        id: str = None,
        input_links: typing.Mapping[str, typing.Any] = None,
        workflow_id: str = None,
        doc: str = None,
    ):

        if isinstance(processing_config, typing.Mapping):
            p_type = processing_config.get(MODULE_TYPE_KEY, None)
            if p_type is None:
                processing_config = dict(processing_config)
                processing_config[MODULE_TYPE_KEY] = "workflow"
            elif p_type != "workflow":
                raise ValueError(f"Invalid module_name for workflow: {p_type}")

        self._workflow_doc: typing.Optional[str] = doc

        self._processing_obj: WorkflowProcessingModule

        super().__init__(
            processing_config=processing_config,
            id=id,
            input_links=input_links,
            workflow_id=workflow_id,
        )
        self._processing_obj.set_workflow_id(self.id)

        if not isinstance(self._processing_obj, WorkflowProcessingModule):
            raise TypeError(
                f"Invalid class for processing object in workflow: {self._processing_obj.__class__}"
            )

    async def _process_workflow(self, executor: Processor = None):

        await self._processing_obj._process_workflow(
            self._current_inputs,
            self._current_outputs,
            executor=executor,
            workflow_id=self.id,
        )

    @property
    def is_workflow(self) -> bool:
        return True

    @property
    def structure(self) -> WorkflowStructure:
        return self._processing_obj.structure  # type: ignore

    @property
    def doc(self) -> str:
        if self._workflow_doc:
            return self._workflow_doc
        else:
            return self._processing_obj.doc
