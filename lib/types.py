from __future__ import annotations

import typing

T = typing.TypeVar("T")
Generator = typing.Generator[T, None, None]  # py313/PEP696 shim
Environ = typing.MutableMapping[str, str]
Callback = typing.Callable[[], T]
