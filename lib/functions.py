from __future__ import annotations

import datetime
from typing import Iterable
from typing import TypeVar

from .types import Lines

T = TypeVar("T")


class MoreThanOneError(AssertionError):
    pass


class LessThanOneError(AssertionError):
    pass


def now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


def one(xs: Iterable[T]) -> T:
    __tracebackhide__ = True

    tmp = tuple(xs)
    count = len(tmp)
    if count == 1:
        return tmp[0]
    elif count < 1:
        raise LessThanOneError(f"Expected one result, got zero: {tmp}")
    else:  # count > 1:
        raise MoreThanOneError(f"Expected one result, got {count}: {tmp}")


def noop() -> None:
    pass


def config_lines(lines: Lines) -> Lines:
    """Strip commented and empty lines from configuration."""
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        yield line
