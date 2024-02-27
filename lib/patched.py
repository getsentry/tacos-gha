from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from lib.constants import UNSET

if TYPE_CHECKING:
    from typing import Generator

    Vars = dict[str, object]


@contextlib.contextmanager
def patched(obj: object, **attrs: object) -> Generator[Vars, None, None]:
    oldattrs: dict[str, object] = {}
    for attr, value in attrs.items():
        oldattrs[attr] = getattr(obj, attr, UNSET)
        setattr(obj, attr, value)

    try:
        yield oldattrs

    finally:
        for attr, value in oldattrs.items():
            if value is UNSET:
                delattr(obj, attr)
            else:
                setattr(obj, attr, value)
