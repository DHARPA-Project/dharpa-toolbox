# -*- coding: utf-8 -*-

__all__ = [
    "get_auto_module_id",
    "ValueLocationType",
    "ValueLocation",
    "ModuleState",
    "DharpaModule",
    "EmptyObject",
    "find_all_module_classes",
]

import logging
import typing
from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import Mapping

from traitlets import All, Bool, Dict, HasTraits, Instance

from ..utils import get_module_name_from_class, get_subclass_map


log = logging.getLogger("dharpa-toolbox")

_AUTO_MODULE_ID: Dict[typing.Type, int] = {}


def get_auto_module_id(module_cls: typing.Type):

    nr = _AUTO_MODULE_ID.setdefault(module_cls, 0)
    _AUTO_MODULE_ID[module_cls] = nr + 1

    name = get_module_name_from_class(module_cls)

    return f"{name}_{nr}"


class ValueLocationType(Enum):
    input = 2
    output = 3


class ValueLocation(typing.NamedTuple):
    module: "DharpaModule"
    value_name: str
    type: ValueLocationType

    def __hash__(self):

        return hash((self.module, self.value_name, self.type))

    def __eq__(self, other):

        if not isinstance(other, ValueLocation):
            return False

        return (self.module, self.value_name, self.type) == (
            other.module,
            other.value_name,
            other.type,
        )

    def __str__(self):

        if self.type == ValueLocationType.output:
            t = f"{self.module.id} output"
        elif self.type == ValueLocationType.workflow_input:
            t = "user_input"
        elif self.type == ValueLocationType.workflow_output:
            t = "result"
        else:
            t = f"{self.module.id} input"

        # return f"{self.module.id}.{t}.{self.value_name}"
        return f"{t}: {self.value_name}"
        # return f"{self.module.id} {t}: {self.value_name}"


class ModuleState(HasTraits):

    config = Dict(allow_none=False)

    inputs = Instance(klass=HasTraits, allow_none=False)
    outputs = Instance(klass=HasTraits, allow_none=False)

    stale = Bool(default_value=True)
    busy = Bool(default_value=False)


class DharpaModule(metaclass=ABCMeta):
    def __init__(self, **config: typing.Any):

        _id = config.pop("id", None)
        if _id is None:
            _id = get_auto_module_id(self.__class__)

        if "." in _id:
            raise ValueError(f"Module id can't contain '.': {_id}")
        if not isinstance(_id, str):
            raise TypeError(
                f"Can't create module, module id must be of type string, not {type(_id)}: {_id}"
            )

        self._id: str = _id
        self._config_raw: Mapping[str, typing.Any] = None  # type: ignore

        self._input_locations: Mapping[str, ValueLocation] = None  # type: ignore
        self._output_locations: Mapping[str, ValueLocation] = None  # type: ignore

        self._input_current: typing.Dict[str, typing.Any] = {}  # type: ignore
        self._input_staging: typing.Dict[str, typing.Any] = {}  # type: ignore

        self._state: ModuleState = None  # type: ignore
        self.set_config(**config)

    @abstractmethod
    def _process(self, **inputs: typing.Any) -> Mapping[str, typing.Any]:
        """Method to implement that processes the input.

        The result must be a Mapping with the output names as keys, and the output values as, well... values.

        Args:
            **inputs (Any): the (current) inputs of this module

        Returns:
            Mapping[str, Any]: the result values of this module as a dictionary
        """
        pass

    @abstractmethod
    def _create_inputs(self, **config) -> HasTraits:
        pass

    @abstractmethod
    def _create_outputs(self, **config) -> HasTraits:
        pass

    def set_config(self, **config: typing.Any):
        """Set the config of this module.

        Does some general sanitiy checking, as well as setting the initial state of the module.
        Whenever this method is called, the current input/output traitlets will be removed and new objects will be created.

        Args:
            **config (Any): the configuration

        """

        # module id must stay the same
        if "id" in config.keys() and config["id"] != self.id:
            raise ValueError(
                f"Changing module id is not allowed: {self.id} != {config['id']}"
            )

        # we store the unprocessed config, so we have the option to do some diff-ing later on, and for debugging
        self._config_raw = config
        # pre-process the configuration, this is heavily used in the 'workflow' class, but the '_preprocess_config'
        # method can be overwritten by any class that inherits from this. By default the raw configuration will
        # not be modified
        processed_config = self._preprocess_config(**self._config_raw)

        # delete the current values for the 'staging' level of the input, as well as any potential values
        # that were already processed. Also clear the input/output wrapper objects.
        self._input_staging = {}
        self._input_current = {}

        if self._state is None:
            # create a new state object if the configuration is set for the first time

            self._state = ModuleState(
                config=processed_config,
                inputs=self._create_inputs(**processed_config),
                outputs=self._create_outputs(**processed_config),
                stale=True,
                busy=False,
            )
        else:
            # remote all observers and clear state if the configuration was already set earlier
            self._state.inputs.unobserve_all()
            self._state.outputs.unobserve_all()

            self._state.config = processed_config

            self._state.inputs = self._create_inputs(**self._state.config)
            self._state.outputs = self._create_outputs(**self._state.config)

        # create input/output wrapper objects -- those will be used by 'parent' workflows, as well as input/output
        # widgets
        new_input_locations = {}
        for name in self._state.inputs.trait_names():
            new_input_locations[name] = ValueLocation(
                module=self, value_name=name, type=ValueLocationType.input
            )
        self._input_locations = new_input_locations
        new_output_locations = {}
        for name in self._state.outputs.trait_names():
            new_output_locations[name] = ValueLocation(
                module=self, value_name=name, type=ValueLocationType.output
            )
        self._output_locations = new_output_locations

        # listen to events where inputs are set
        self._state.inputs.observe(self._input_updated, names=All)
        # set the initial state of this module where there is no input yet to 'stale'
        self._state.stale = True

    def _preprocess_config(self, **config: typing.Any):
        """(Optionally) preprocess the configuration.

        In most cases this method can be ignored. Sometimes it's useful to validate or augment configuration, in which
        case an implementing class can do this here.
        """

        return config

    def set_config_value(self, key: str, value: typing.Any):
        """Set a configuration value.

        Using this method will call 'set_config', and re-initialize the module.

        Args:
            key (str): the config key
            value (Any): the config value
        """

        if key == "id":
            raise ValueError("Changing module id is not allowed.")

        _config_new = dict(self._config_raw)
        _config_new[key] = value
        self.set_config(**_config_new)

    def get_input_location(self, value_name: str) -> ValueLocation:
        """Retrieve an input value wrapping object from a string."""

        return self._input_locations[value_name]

    def get_output_location(self, value_name: str) -> ValueLocation:
        """Retrieve an output value wrapping object from a string."""

        return self._output_locations[value_name]

    # @property
    # def inputs(self) -> HasTraits:
    #
    #     return self._state.inputs

    def set_input(self, input_name: str, value: typing.Any) -> None:
        """Set an input value of this module.

        Args:
            input_name (str): the name of the input
            value (Any): the value
        """

        print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
        print(self)
        print(self._state.inputs.trait_names())

        self._state.inputs.set_trait(input_name, value)

    # @property
    # def outputs(self) -> HasTraits:
    #
    #     return self._state.outputs

    def _input_updated(self, change) -> typing.Any:

        log.debug(f"Input updated for module ({self.id}): {change}")

        if change.name not in self._input_staging.keys():
            self._input_staging[change.name] = {"old": change.old, "new": change.new}
        else:
            self._input_staging[change.name]["new"] = change.new
        self._state.stale = True

    def process(self):
        """Process this modules current inputs."""

        self._state.busy = True  # if not self._stale_state:
        #     return

        try:

            current = {}
            for k in self._state.inputs.trait_names():
                v = getattr(self._state.inputs, k)
                current[k] = v

            result = self._process(**current)

            # print("RESULT")
            # print(result)
            self._inputs_current.clear()
            self._inputs_current.update(current)

            self._input_staging.clear()

            with self._state.outputs.hold_trait_notifications():
                if result:
                    for k, v in result.items():

                        if k not in self._state.outputs.trait_names():
                            continue
                        self._state.outputs.set_trait(k, v)
                self._state.stale = False

        # except Exception as e:
        #     raise
        finally:
            self._state.busy = False

    @property
    def id(self) -> str:
        return self._id

    @property
    def stale(self) -> bool:
        return self._state.stale

    @property
    def busy(self) -> bool:
        return self._state.busy

    @property
    def state(self) -> HasTraits:
        return self._state

    @property
    def current_state(self) -> typing.Dict[str, typing.Any]:

        result: Dict[str, typing.Any] = {"inputs": {}, "outputs": {}}
        for tn in self._state.inputs.trait_names():
            stale = False
            result["inputs"][tn] = {}
            if tn in self._input_current.keys():
                result["inputs"][tn]["current_value"] = self._input_current[tn]
            else:
                stale = True
                result["inputs"][tn]["current_value"] = "-- not set --"

            if tn in self._input_staging.keys():
                stale = True
                result["inputs"][tn]["new_value"] = self._input_staging[tn]["new"]
            else:
                result["inputs"][tn]["new_value"] = "-- not set --"
            result["inputs"][tn]["stale"] = stale

        for tn in self._state.outputs.trait_names():
            result["outputs"][tn] = getattr(self._state.outputs, tn)

        result["stale"] = self._state.stale
        return result

    @property
    def input_names(self) -> typing.Iterable[str]:

        return self._state.inputs.trait_names()

    @property
    def output_names(self) -> typing.Iterable[str]:
        return self._state.outputs.trait_names()

    def __eq__(self, other):

        if self.__class__ != other.__class__:
            return False

        return self.id == other.id

    def __hash__(self):

        return hash(self.id)

    def __repr__(self):

        return f"{self.__class__.__name__}(id='{self.id}' input_names={self._state.inputs.trait_names()} output_names={self._state.outputs.trait_names()}) config={self._config_raw}"

    def __str__(self):

        return f"module: '{self.id}'"


class EmptyObject(HasTraits):

    pass


# Cell


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
    )
    return all_module_clases
