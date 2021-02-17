# -*- coding: utf-8 -*-
import typing
from abc import ABCMeta, abstractmethod

from dharpa.data.core import DataSchema
from dharpa.utils import get_module_name_from_class
from pydantic import BaseModel


if typing.TYPE_CHECKING:
    from dharpa.workflows.modules import InputItems, OutputItems

_AUTO_MODULE_ID: typing.Dict[str, int] = {}
"""Global variable to store unique/used module ids per type."""


def get_auto_module_id(
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


class ProcessingModuleConfig(BaseModel):
    pass


class ProcessingModule(metaclass=ABCMeta):
    def __init__(self, **config: typing.Any):

        self._config: ProcessingModuleConfig = self._processing_step_config_cls()(
            **config
        )

        self._input_schemas: typing.Mapping[str, DataSchema] = None  # type: ignore
        self._output_schemas: typing.Mapping[str, DataSchema] = None  # type: ignore

    @property
    def config(self) -> typing.Mapping[str, typing.Any]:
        return self._config.dict()

    @property
    def input_names(self) -> typing.Iterable[str]:
        return self.input_schemas.keys()

    @property
    def output_names(self) -> typing.Iterable[str]:
        return self.output_schemas.keys()

    @property
    def input_schemas(self) -> typing.Mapping[str, DataSchema]:
        if self._input_schemas is None:
            self._input_schemas = self._create_input_schema()
        return self._input_schemas

    @property
    def output_schemas(self) -> typing.Mapping[str, DataSchema]:
        if self._output_schemas is None:
            self._output_schemas = self._create_output_schema()
        return self._output_schemas

    @abstractmethod
    def _create_input_schema(self) -> typing.Mapping[str, DataSchema]:
        pass

    @abstractmethod
    def _create_output_schema(self) -> typing.Mapping[str, DataSchema]:
        pass

    @abstractmethod
    def _process(self, inputs: "InputItems", outputs: "OutputItems") -> None:
        pass

    def _processing_step_config_cls(self) -> typing.Type[ProcessingModuleConfig]:
        return ProcessingModuleConfig

    def process(self, inputs: "InputItems", outputs: "OutputItems") -> None:

        self._process(inputs=inputs, outputs=outputs)

    def __eq__(self, other):

        if self.__class__ != other.__class__:
            return False

        return self.id == other.id

    def __hash__(self):

        return hash(self.id)

    def __repr__(self):

        return f"{self.__class__.__name__}(id='{self.id}' input_names={self.input_names} output_names={self.output_names})"
