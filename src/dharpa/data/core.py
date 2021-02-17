# -*- coding: utf-8 -*-
import collections
import copy
import typing
import uuid
from enum import Enum


class DataType(Enum):
    def __new__(cls, *args, **kwds):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, type_map: typing.Mapping[str, typing.Any]):

        for k, v in type_map.items():
            setattr(self, k, v)

    integer = {"python": int}
    string = {"python": str}
    dict = {"python": dict}
    boolean = {"python": bool}


class DataSchema(object):
    def __init__(
        self, type: DataType, default: typing.Any = None, nullable: bool = False
    ):

        self._type: DataType = type
        self._default: typing.Any = default
        self._nullable: bool = nullable

    @property
    def type(self) -> DataType:
        return self._type

    @property
    def default(self) -> typing.Any:
        return self._default

    @property
    def nullable(self) -> bool:
        return self._nullable

    def create_data_item(self) -> "DataItem":

        item = DataItem(self)
        return item

    def __repr__(self):

        return f"{self.__class__.__name__}(type={self.type.name})"


class DataItem(object):
    def __init__(self, schema: DataSchema):

        self._id: str = str(uuid.uuid4())
        self._schema = schema
        self._value: typing.Any = None

        self._is_streaming: bool = False

        if self._schema.default:
            if callable(self._schema.default):
                self._data: typing.Any = self._schema.default()
            else:
                self._data = copy.deepcopy(self._schema.default)

        self._callbacks: typing.List[typing.Callable] = []

    @property
    def schema(self) -> DataSchema:
        return self._schema

    @property
    def value(self) -> typing.Any:
        return self._value

    @value.setter
    def value(self, value: typing.Any):
        self.set_value(value)

    def set_value(self, value: typing.Any):
        self._pre_value_set(value)
        old_value = self._value
        self._value = value
        self._post_value_set(old_value)
        self._is_streaming = False

    @property
    def valid(self) -> bool:
        return self._value is not None

    def _pre_value_set(self, value_to_set: typing.Any):
        pass

    def _post_value_set(self, old_value: typing.Any):

        for cb in self._callbacks:
            cb(self.value)

    @property
    def is_streaming(self) -> bool:
        return self._is_streaming

    def add_callback(self, callback: typing.Callable):
        self._callbacks.append(callback)

    def __hash__(self):

        return hash(self._id)

    def __eq__(self, other):

        if not isinstance(other, DataItem):
            return False
        return self._id == other._id

    def __repr__(self):

        return f"DataItem(value={self.value} valid={self.valid})"


class DataItems(collections.abc.MutableMapping):
    def __init__(self, **items: DataItem):

        super(DataItems, self).__setattr__("_data_items", items)

    def __getattr__(self, item):

        if item == "_data_items":
            raise KeyError()
        if item == "ALL":
            return {k: v.value for k, v in self.__dict__["_data_items"].items()}
        elif item in self.__dict__["_data_items"].keys():
            return self.__dict__["_data_items"][item].value
        else:
            return super().__getattribute__(item)

    def __setattr__(self, key, value):

        if key == "ALL":
            self.set_values(**value)
        elif key in self._data_items.keys():
            self.set_values(**{key: value})
        elif key.startswith("_") or key.startswith("items__"):
            self.__dict__[key] = value

    def __getitem__(self, item):

        return self._data_items[item]

    def __setitem__(self, key, value):

        self.set_values(**{key: value})

    def __delitem__(self, key):

        raise Exception(f"Removing items not supported: {key}")

    def __iter__(self):
        return iter(self._data_items)

    def __len__(self):
        return len(self._data_items)

    @property
    def items__is_valid(self) -> bool:

        for item in self._data_items.values():
            if not item.valid:
                return False
        return True

    def _pre_values_set(self, values_to_set: typing.Mapping[str, typing.Any]):
        pass

    def _post_values_set(self, old_values: typing.Mapping[str, typing.Any]):
        pass

    def set_values(self, **values: typing.Any) -> None:

        invalid = []
        for k, v in values.items():
            if k not in self._data_items.keys():
                invalid.append(k)

        if invalid:
            raise ValueError(
                f"No data item(s) with name(s) {', '.join(invalid)} available, valid names: {', '.join(self._data_items.keys())}"
            )

        self._pre_values_set(values)
        old_values = {}
        for k, v in values.items():
            old_values[k] = self._data_items[k].value
            self._data_items[k].value = v
        self._post_values_set(old_values)

    def __repr__(self):

        return f"DataItems(value_names={list(self._data_items.keys())} valid={self.items__is_valid})"
