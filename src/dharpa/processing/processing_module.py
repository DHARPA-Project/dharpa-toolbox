# -*- coding: utf-8 -*-
import inspect
import typing
from abc import ABCMeta, abstractmethod

from dharpa.data.core import DataSchema
from dharpa.models import ProcessingModuleConfig


if typing.TYPE_CHECKING:
    from dharpa.workflows.modules import InputItems, OutputItems

"""Global variable to store unique/used module ids per type."""


class ProcessingModule(metaclass=ABCMeta):

    _processing_step_config_cls: typing.Type[
        ProcessingModuleConfig
    ] = ProcessingModuleConfig

    def __init__(self, **config: typing.Any):

        self._config: ProcessingModuleConfig = (
            self.__class__._processing_step_config_cls(**config)
        )

        self._input_schemas: typing.Mapping[str, DataSchema] = None  # type: ignore
        self._output_schemas: typing.Mapping[str, DataSchema] = None  # type: ignore

        self._doc: str = None  # type: ignore

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

    @property
    def doc(self) -> str:
        if self._doc is None:
            self._doc = self._get_doc()
        return self._doc

    def _get_doc(self) -> str:

        doc = self.__doc__
        if not doc:
            try:
                doc = self.__init__.__doc__  # type: ignore
            except Exception:
                pass

        if not doc:
            return "-- n/a --"
        else:
            doc = inspect.cleandoc(doc)
            return doc

    @abstractmethod
    def _create_input_schema(self) -> typing.Mapping[str, DataSchema]:
        pass

    @abstractmethod
    def _create_output_schema(self) -> typing.Mapping[str, DataSchema]:
        pass

    @abstractmethod
    async def _process(self, inputs: "InputItems", outputs: "OutputItems") -> None:
        pass

    async def process(self, inputs: "InputItems", outputs: "OutputItems") -> None:

        await self._process(inputs=inputs, outputs=outputs)

    def __eq__(self, other):

        if self.__class__ != other.__class__:
            return False

        return self.config == other.config

    def __hash__(self):

        return hash(self.config)

    def __repr__(self):

        return f"{self.__class__.__name__}(input_names={self.input_names} output_names={self.output_names})"


class ProcessingBundle(object):
    def __init__(
        self, type: str, config: typing.Mapping[str, typing.Any], inputs: "InputItems"
    ):

        self._processing_module_type: str = type
        self._module_config: typing.Mapping[str, typing.Any] = config
        self._inputs: InputItems = inputs
