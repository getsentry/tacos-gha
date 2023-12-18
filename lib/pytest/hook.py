from __future__ import annotations

from typing import ContextManager

from lib.types import Callback


def beforeafter(
    context: Callback[ContextManager[None]],
) -> tuple[Callback[None], Callback[None]]:
    _context = context()

    def after():
        from sys import exc_info

        _context.__exit__(*exc_info())

    return _context.__enter__, after
