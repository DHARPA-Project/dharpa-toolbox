# -*- coding: utf-8 -*-
# AUTOGENERATED! DO NOT EDIT! File to edit: notebooks/99_utils.ipynb (unless otherwise specified).

__all__ = [
    "load_modules",
    "get_all_subclasses",
    "get_subclass_map",
    "get_snake_case_from_class",
    "to_camel_case",
    "get_module_name_from_class",
    "graph_to_image",
    "log",
]

# Cell

# export
import collections.abc
import importlib
import inspect
import logging
import re
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Type, Union

import networkx as nx
from IPython.display import Image


log = logging.getLogger("dharpa-toolbox")

_PRELOADED = []


def load_modules(modules: Union[None, str, Iterable[str]]) -> bool:
    """Load all specified modules by (string-)name.

    If an item ends with '.*', all child modules will be loaded. No other
    wildcards/wildcard positions are supported for now.

    Args:
        *modules: a list of modules

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
):

    if preload_modules:
        load_modules(preload_modules)

    all_subclasses = []
    for subclass in cls.__subclasses__():
        if not inspect.isabstract(subclass) or include_abstract_classes:
            all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


def get_subclass_map(
    cls: Type,
    include_abstract_classes: bool = False,
    preload_modules: Union[Iterable[str], str, None] = None,
    key_func: Optional[Callable] = None,
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
        if key in result.keys():
            raise Exception(f"Duplicate subclass key: {key}")
        result[key] = sc

    return result


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


def get_module_name_from_class(cls: Type):

    if hasattr(cls, "_module_name"):
        return cls._module_name
    else:
        return get_snake_case_from_class(cls)


def graph_to_image(graph: nx.Graph):
    try:
        import pygraphviz as pgv  # noqa
    except:  # noqa
        return "pygraphviz not available"

    G = nx.nx_agraph.to_agraph(graph)

    G.node_attr["shape"] = "box"
    G.layout(prog="dot")

    b = G.draw(format="png")

    return Image(b)
