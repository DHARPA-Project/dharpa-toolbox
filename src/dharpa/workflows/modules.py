# -*- coding: utf-8 -*-
import collections
import sys
import typing
from functools import partial

from dharpa.data.core import DataItem, DataItems, DataSchema
from dharpa.models import (
    ModuleDetails,
    ModuleState,
    ProcessingConfig,
    ValueItem,
    ValueSchema,
)
from dharpa.processing.executors import Processor
from dharpa.processing.processing_module import ProcessingModule
from dharpa.workflows.utils import get_auto_module_alias


def explode_input_links(
    input_links: typing.Any,
) -> typing.Mapping[str, typing.Mapping[str, str]]:
    """Ensure format of input links is correct.

    Auto-fill shortened links if necessary, this makes configuration on the user-side easier.
    """

    if input_links is None:
        input_links = {}

    result: typing.Dict[str, typing.Mapping[str, str]] = {}
    for input_name, output in input_links.items():
        if isinstance(output, str):
            if "." in output:
                module_id, output_name = output.rsplit(".", maxsplit=1)
            else:
                module_id = output
                output_name = input_name
        elif isinstance(output, collections.abc.Mapping):
            module_id = output["module_id"]
            output_name = output["output_name"]
        elif isinstance(output, collections.abc.Sequence) and len(output) == 2:
            module_id = output[0]
            output_name = output[1]
        else:
            raise TypeError(f"Can't parse input map, invalid type for output: {output}")

        result[input_name] = {"module_id": module_id, "value_name": output_name}

    return result


class InputItems(DataItems):
    def __init__(
        self,
        **items: DataSchema,
    ):

        _data_items: typing.Dict[str, DataItem] = {}

        for name, item in items.items():
            try:
                _data_items[name] = item.create_data_item()
            except Exception as e:
                raise Exception(f"Can't create data item '{name}': {e}")

        super().__init__(**_data_items)
        # self._id: str = id
        self._input_allowed: bool = True

    # @property
    # def items__id(self):
    #     return self._id

    @property
    def items__input_allowed(self) -> bool:
        return self._input_allowed

    def items__disable(self) -> None:
        self._input_allowed = False

    def items__enable(self) -> None:
        self._input_allowed = True

    def _pre_values_set(self, new_values: typing.Mapping[str, typing.Any]):

        if not self._input_allowed:
            raise Exception("Setting input not allowed at the moment.")

    def _post_values_set(self, old_values: typing.Mapping[str, typing.Any]):
        pass

    def __repr__(self):

        return f"InputItems(value_names={list(self._data_items.keys())} valid={self.items__are_valid})"


class OutputItems(DataItems):
    def __init__(
        self,
        **items: DataSchema,
    ):

        _data_items: typing.Dict[str, DataItem] = {}

        for name, item in items.items():
            try:
                _data_items[name] = item.create_data_item()
            except Exception as e:
                raise Exception(f"Can't create data item '{name}': {e}")

        super().__init__(**_data_items)
        # self._id: str = id
        self._state: ModuleState = ModuleState.STALE

    # @property
    # def items__id(self):
    #     return self._id

    def __repr__(self):

        return f"OutputItems(value_names={list(self._data_items.keys())} valid={self.items__are_valid} state={self._state.name})"


class WorkflowModule(object):
    def __init__(
        self,
        processing_config: typing.Union[
            ProcessingConfig, typing.Mapping[str, typing.Any]
        ],
        alias: str = None,
        workflow_id: str = None,
        input_links: typing.Mapping[str, typing.Any] = None,
    ):

        if isinstance(processing_config, typing.Mapping):
            _processing_config: ProcessingConfig = ProcessingConfig.from_dict(
                **processing_config
            )
        else:
            _processing_config = processing_config

        if not alias:
            alias = get_auto_module_alias(_processing_config.module_type)

        self._workflow_id: typing.Optional[str] = workflow_id
        self._alias: str = alias
        self._state: ModuleState = ModuleState.STALE
        self._is_processing: bool = False
        self._processing_config: ProcessingConfig = _processing_config
        self._execution_stage: typing.Optional[int] = None

        self._processing_obj: ProcessingModule = (
            self._processing_config.create_processing_module()
        )

        self._input_connection_map: typing.Mapping[
            str, typing.Mapping[str, str]
        ] = explode_input_links(input_links)
        self._current_inputs: InputItems = InputItems(**self.input_schema)
        for name, item in self._current_inputs.items():
            func = partial(self._input_changed, name)
            item.add_callback(func)

        self._current_outputs: OutputItems = OutputItems(**self.output_schema)

        # self._zmq_context: zmq.Context = zmq.Context.instance()
        # self._module_event_socket: zmq.Socket = self._zmq_context.socket(zmq.PUSH)
        # if self._workflow_id:
        #     self._module_event_socket.connect(f"inproc://{self.workflow_id}")

    @property
    def alias(self) -> str:
        return self._alias

    @property
    def address(self) -> str:
        if self._workflow_id:
            return f"{self._workflow_id}.{self._alias}"
        else:
            return self._alias

    @property
    def module_type(self) -> str:
        return self._processing_obj._module_name  # type: ignore

    @property
    def is_pipeline(self) -> bool:
        return False

    @property
    def execution_stage(self) -> typing.Optional[int]:
        return self._execution_stage

    @execution_stage.setter
    def execution_stage(self, stage: int):
        self._execution_stage = stage

    @property
    def workflow_id(self) -> typing.Optional[str]:
        return self._workflow_id

    @property
    def doc(self) -> str:
        return self._processing_obj.doc

    @property
    def input_connection_map(self) -> typing.Mapping[str, typing.Mapping[str, str]]:
        return self._input_connection_map

    @property
    def input_schema(self) -> typing.Mapping[str, DataSchema]:
        return self._processing_obj.input_schemas

    @property
    def output_schema(self) -> typing.Mapping[str, DataSchema]:
        return self._processing_obj.output_schemas

    @property
    def inputs(self) -> InputItems:
        return self._current_inputs

    @inputs.setter
    def inputs(self, inputs: typing.Any):
        self._current_inputs.set_values(**inputs)

    def _input_changed(self, input_name: str, new_value: typing.Any):

        self._update_state()

    @property
    def state(self) -> ModuleState:
        if self._state == ModuleState.STALE:
            if self.inputs.items__are_valid:
                self._state = ModuleState.INPUTS_READY
        return self._state

    @property
    def is_processing(self) -> bool:
        return self._is_processing

    def _update_state(self) -> ModuleState:

        # current = self._state
        if not self.inputs.items__are_valid:
            new_state = ModuleState.STALE
        elif not self.outputs.items__are_valid:
            new_state = ModuleState.INPUTS_READY
        else:
            new_state = ModuleState.RESULTS_READY

        self._state = new_state

        # if current != new_state:
        #     print(f"{self} - new state: {self._state}")

        # if current != new_state:
        #     module_event = ModuleEvent(ModuleEventType.state_changed, module_id=self.id, old_state=current.name, new_state=new_state.name)
        #     self._module_event_socket.send_json(module_event.to_dict())

        return self._state

    def _outputs_changed(self, outputs: OutputItems):

        self._update_state()

    async def process(self, executor: Processor = None):

        print(f"processing started: {self.address}", file=sys.stderr)

        self._state = ModuleState.RESULTS_INCOMING
        self._current_inputs.items__disable()

        # print(f"process started: {self} {executor}")

        try:

            if self.is_pipeline:
                # workflows need to have access to the executor directly
                await self._process_workflow(executor=executor)  # type: ignore
            else:
                if executor is None:
                    await self._processing_obj.process(
                        self._current_inputs, self._current_outputs
                    )
                else:
                    if self._state == ModuleState.STALE:
                        missing = []
                        for k, v in self.inputs.items():
                            if v.value is None:
                                missing.append(k)
                        raise Exception(
                            f"Can't start processing for module '{self.alias}', inputs not ready yet: {missing}"
                        )

                    # raise NotImplementedError()
                    await executor.process(self)

            self._current_inputs.items__enable()
            # print(f"process finished: {self}")

            self._update_state()
        except Exception as e:
            print(
                f"processing '{self.address}' finished with error: {e}", file=sys.stderr
            )
            raise e
        finally:
            print(f"processing finished: {self.address}", file=sys.stderr)

    @property
    def outputs(self) -> OutputItems:
        return self._current_outputs

    def to_details(self) -> ModuleDetails:
        inputs = {}
        for k, v in self.inputs.items():
            i = ValueItem(
                schema=ValueSchema(type=v.schema.type, default=v.schema.default),
                value=v.value,
            )
            inputs[k] = i
        outputs = {}
        for k, v in self.outputs.items():
            o = ValueItem(
                schema=ValueSchema(type=v.schema.type, default=v.schema.default),
                value=v.value,
            )
            outputs[k] = o

        return ModuleDetails(
            alias=self.alias,
            address=self.address,
            type=self.module_type,
            is_pipeline=self.is_pipeline,
            execution_stage=self.execution_stage,
            state=self.state,
            inputs=inputs,
            outputs=outputs,
            doc=self.doc,
        )

    def to_dict(self, exclude_none: bool = False) -> typing.Dict[str, typing.Any]:

        details = self.to_details()
        return details.dict(by_alias=True, exclude_none=exclude_none)

    def to_json(self, exclude_none: bool = False, **dump_kwargs: typing.Any) -> str:

        details = self.to_details()
        return details.json(by_alias=True, exclude_none=exclude_none, **dump_kwargs)

    def __repr__(self):

        if self.execution_stage:
            exc_stage = f" execution_stage={self.execution_stage}"
        else:
            exc_stage = ""

        return f"{self.__class__.__name__}(alias={self.alias} workflow={self.is_pipeline}{exc_stage})"

    # def __str__(self):
    #
    #     return self.id
