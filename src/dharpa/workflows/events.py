# -*- coding: utf-8 -*-
import typing
from enum import Enum
from pydantic import BaseModel


class StateChangedEvent(BaseModel):

    module_id: str
    old_state: str
    new_state: str


class InputChangedEvent(BaseModel):

    module_id: str
    input_name: str


class OutputChangedEvent(BaseModel):

    module_id: str
    output_name: str


class SetInputEvent(BaseModel):

    module_id: str
    input_name: str
    value: typing.Any


class ModuleEventType(Enum):
    def __new__(cls, *args, **kwds):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, event_cls: typing.Type[BaseModel]):

        self._event_cls: typing.Type[BaseModel] = event_cls

    def create_event(self, **details: typing.Any):

        return self._event_cls(**details)

    state_changed = StateChangedEvent
    input_changed = InputChangedEvent
    output_changed = OutputChangedEvent
    set_input = SetInputEvent


class ModuleEvent(object):
    @classmethod
    def from_dict(self, **details):

        event_type_name = details.pop("event_type")
        event_type = ModuleEventType[event_type_name]

        result = ModuleEvent(event_type=event_type, **details)
        return result

    def __init__(self, event_type: ModuleEventType, **details):

        self._event_type: ModuleEventType = event_type
        self._event_obj: BaseModel = self._event_type.create_event(**details)

    @property
    def event_type(self) -> ModuleEventType:
        return self._event_type

    @property
    def event_obj(self) -> BaseModel:
        return self._event_obj

    def to_dict(self):

        result = self._event_obj.dict()
        result["event_type"] = self._event_type.name
        return result
