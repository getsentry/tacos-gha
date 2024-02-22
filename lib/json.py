#!/usr/bin/env py.test
"""Types and tools for dealing with JSON data."""

from __future__ import annotations

import typing
from collections.abc import Mapping
from collections.abc import Sequence

from lib.types import OSPath

T = typing.TypeVar("T")
Primitive = str | int | float | bool | None
Object = Mapping[str, "Value"]
Array = Sequence["Value"]
Value = Primitive | Array | Object


def assert_dict_of_strings(json: Value) -> dict[str, str]:
    assert isinstance(json, dict), json
    for key, val in json.items():
        assert isinstance(key, str), (key, json)
        assert isinstance(val, str), (val, json)
    # https://github.com/microsoft/pyright/discussions/6577
    return typing.cast(dict[str, str], json)


def load(path: OSPath) -> Value:
    from json import load

    return typing.cast(Value, load(path.open()))


def get(json: Value, result_type: type[T], key: int | str) -> T:
    """Get a value from a json structure, with type safety.

    >>> json = {"a": 2}
    >>> get(json, int, 'a')
    2

    >>> json = ["red", "blue"]
    >>> get(json, str, 1)
    'blue'
    """
    result = json
    if isinstance(key, str):
        assert isinstance(result, dict), result
        result = result[key]
    else:  # if isinstance(key, int):
        assert isinstance(result, list), result
        result = result[key]

    assert isinstance(result, result_type)
    return result


def deepget(json: Value, result_type: type[T], *keys: int | str) -> T:
    """Get a value from a deep json structure, with type safety.

    >>> json = [{"a": {"b": [1, 2]}}]
    >>> deepget(json, int, 0, 'a', 'b', 1)
    2
    """
    result = json
    for key in keys:
        if isinstance(key, str):
            assert isinstance(result, dict), result
            result = result[key]
        else:  # if isinstance(key, int):
            assert isinstance(result, list), result
            result = result[key]

    assert isinstance(result, result_type)
    return result
