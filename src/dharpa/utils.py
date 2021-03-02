# -*- coding: utf-8 -*-
import collections.abc
import importlib
import inspect
import json
import logging
import os
import re
import typing
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Set, Type, Union

import yaml


log = logging.getLogger("dharpa")

if typing.TYPE_CHECKING:
    pass

_PRELOADED = []


_NAME_FIRST = re.compile("(.)([A-Z][a-z]+)")
_NAME_ALL = re.compile("([a-z0-9])([A-Z])")


def get_snake_case_from_class(
    cls: Type,
):

    text = cls.__name__

    sep = "_"
    text = _NAME_FIRST.sub(fr"\1{sep}\2", text)
    text = _NAME_ALL.sub(fr"\1{sep}\2", text)

    text = text.lower()

    return text


def to_camel_case(snake_str, capitalize: bool = True):

    first, *others = snake_str.split("_")
    if capitalize:
        first = first.capitalize()
    result = "".join([first, *map(str.capitalize, others)])

    return result


def load_modules(modules: Union[None, str, Iterable[str]]) -> bool:
    """Load all specified processing by (string-)name.

    If an item ends with '.*', all child processing will be loaded. No other
    wildcards/wildcard positions are supported for now.

    Args:
        *modules: a list of processing

    Returns:
        List: a list of module objects that were loaded
    """

    if not modules:
        return False

    if isinstance(modules, str):
        importlib.import_module(modules)
        _PRELOADED.append(modules)
        return True

    result = False

    for mod in modules:
        if not mod:
            continue
        elif isinstance(mod, str) and mod not in _PRELOADED:
            importlib.import_module(mod)
            _PRELOADED.append(mod)
            result = True
        elif isinstance(mod, collections.abc.Iterable):
            r = load_modules(mod)
            if r:
                result = True
        else:
            raise TypeError(f"Invalid module type: {type(mod)}")

    return result


def get_all_subclasses(
    cls: Type,
    include_abstract_classes: bool = False,
    preload_modules: Union[Iterable[str], str, None] = None,
) -> Set[Type]:

    if preload_modules:
        load_modules(preload_modules)

    all_subclasses = set()
    for subclass in cls.__subclasses__():
        if not inspect.isabstract(subclass) or include_abstract_classes:
            all_subclasses.add(subclass)
        all_subclasses.update(get_all_subclasses(subclass))

    return all_subclasses


def get_subclass_map(
    cls: Type,
    include_abstract_classes: bool = False,
    preload_modules: Union[Iterable[str], str, None] = None,
    key_func: Optional[Callable] = None,
    override_duplicate_class: bool = False,
) -> Mapping[str, Type]:

    if key_func is None:
        key_func = lambda _cls: _cls.__name__.lower()  # noqa

    subclasses = get_all_subclasses(
        cls=cls,
        include_abstract_classes=include_abstract_classes,
        preload_modules=preload_modules,
    )

    result: Dict[str, Type[Any]] = {}
    for sc in subclasses:
        key = key_func(sc)
        if key in result.keys() and not override_duplicate_class:
            raise Exception(f"Duplicate subclass key: {key}")
        result[key] = sc

    return {
        key: value for key, value in sorted(result.items(), key=lambda item: item[0])
    }


def get_data_from_file(path: Union[str, Path]):

    if isinstance(path, str):
        path = Path(os.path.expanduser(path))

    content = path.read_text()

    if path.name.endswith(".json"):
        content_type = "json\n"
    elif path.name.endswith(".yaml") or path.name.endswith(".yml"):
        content_type = "yaml\n"
    else:
        raise ValueError(
            "Invalid data format, only 'json' or 'yaml' are supported currently."
        )

    if content_type == "json":
        data = json.loads(content)
    else:
        data = yaml.safe_load(content)

    return data


# def print_file_content(path: Union[str, Path]):
#
#     if isinstance(path, str):
#         path = Path(os.path.expanduser(path))
#
#     content = path.read_text()
#
#     if path.name.endswith(".json"):
#         content_type = "json\n"
#     elif path.name.endswith(".yaml") or path.name.endswith(".yml"):
#         content_type = "yaml\n"
#     else:
#         content_type = ""
#
#     md = Markdown(f"```{content_type}" + content + "```")
#
#     display(md)
