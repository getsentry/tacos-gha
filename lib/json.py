"""Types and tools for dealing with JSON data."""

from __future__ import annotations

from collections.abc import Mapping
from collections.abc import Sequence
from typing import cast

Primitive = str | int | float | bool | None
Object = Mapping[str, Primitive]
Array = Sequence[Primitive]
Value = Primitive | Array | Object


def assert_dict_of_strings(json: Value) -> dict[str, str]:
    assert isinstance(json, dict), json
    for key, val in json.items():
        assert isinstance(key, str), (key, json)
        assert isinstance(val, str), (val, json)
    # https://github.com/microsoft/pyright/discussions/6577
    return cast(dict[str, str], json)
