from __future__ import annotations

from typing import Callable
from typing import ParamSpec
from typing import TypeVar

from lib.sh.io import info

P = ParamSpec("P")
T = TypeVar("T")


class UserError(SystemExit):
    def __init__(self, message: object = None, *, code: int | None = None):
        if code is None:
            code = 1
        super().__init__(code)
        self.message = message
        self.args: tuple[object, ...] = (message,)

    @classmethod
    def handler(cls, func: Callable[P, T]) -> Callable[P, T]:
        from functools import wraps

        @wraps(func)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except cls as error:
                if error.message is not None:
                    info(error.message)
                raise

        return wrapped
