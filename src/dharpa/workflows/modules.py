# -*- coding: utf-8 -*-
import collections
import typing
from enum import Enum
from functools import partial

from dharpa.data.core import DataItem, DataItems, DataSchema
from dharpa.processing.processing_module import ProcessingModule, get_auto_module_id
from dharpa.utils import find_all_module_classes


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


class State(Enum):

    STALE = 0
    INPUTS_READY = 1
    PROCESSING = 2
    RESULTS_READY = 3


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

        return f"InputItems(value_names={list(self._data_items.keys())} valid={self.items__is_valid})"


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
        self._state: State = State.STALE

    # @property
    # def items__id(self):
    #     return self._id

    def __repr__(self):

        return f"OutputItems(value_names={list(self._data_items.keys())} valid={self.items__is_valid} state={self._state.name})"


class WorkflowModule(object):
    def __init__(
        self,
        type: str,
        id: str = None,
        input_links: typing.Mapping[str, typing.Any] = None,
        **config: typing.Any,
    ):

        if not isinstance(type, str):
            raise TypeError(
                f"Invalid type for processing module, must be string: {type}"
            )

        all_modules = find_all_module_classes()

        processing_cls = all_modules.get(type, None)
        if processing_cls is None:
            raise ValueError(
                f"Can't parse config, can't find module type '{type}'. Available modules: {', '.join(all_modules.keys())}"
            )

        if not id:
            id = get_auto_module_id(self.__class__)

        self._id: str = id
        self._state: State = State.STALE
        self._processing_module_type: str = type
        self._processing_module_config = config

        self._processing_obj: ProcessingModule = processing_cls(**config)

        self._input_links: typing.Mapping[
            str, typing.Mapping[str, str]
        ] = explode_input_links(input_links)
        self._current_inputs: InputItems = InputItems(**self.input_schema)
        for name, item in self._current_inputs.items():
            func = partial(self._input_changed, name)
            item.add_callback(func)
        self._current_outputs: OutputItems = OutputItems(**self.output_schema)

    @property
    def id(self) -> str:
        return self._id

    @property
    def input_connection_map(self) -> typing.Mapping[str, typing.Mapping[str, str]]:
        return self._input_links

    @property
    def input_schema(self) -> typing.Mapping[str, DataSchema]:
        return self._processing_obj.input_schemas

    @property
    def output_schema(self) -> typing.Mapping[str, DataSchema]:
        return self._processing_obj.output_schemas

    @property
    def inputs(self) -> InputItems:
        return self._current_inputs

    def _input_changed(self, input_name: str, new_value: typing.Any):
        self._state = State.STALE

    @property
    def state(self) -> State:
        if self._state == State.STALE:
            if self.inputs.items__is_valid:
                self._state = State.INPUTS_READY
        return self._state

    def _outputs_changed(self, outputs: OutputItems):

        if outputs.items__state == State.RESULTS_READY:
            self._state = State.RESULTS_READY
            self._current_inputs.items__enable()

    def process(self):

        self._state = State.PROCESSING
        self._current_inputs.items__disable()

        self._processing_obj.process(self._current_inputs, self._current_outputs)
        self._current_inputs.items__enable()

        if self.outputs.items__is_valid:
            self._state = State.RESULTS_READY
        else:
            self._state = State.STALE

    @property
    def outputs(self) -> OutputItems:
        return self._current_outputs

    def __repr__(self):

        return f"WorkflowModule(id={self.id})"

    def __str__(self):

        return self.id
