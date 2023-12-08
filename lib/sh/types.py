from __future__ import annotations

import typing
from typing import TypeVar

T = TypeVar("T")
Command = tuple[object, ...]
Generator = typing.Generator[T, None, None]  # py313/PEP696 shim
