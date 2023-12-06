# tools for dealing with pytest
# please be responsible; wear eye protection
from __future__ import annotations

import functools
import typing
from contextlib import AbstractContextManager as ContextManager
from typing import Callable
from typing import ParamSpec
from typing import TypeVar

import pytest

T = TypeVar("T")

Generator = typing.Generator[T, None, None]  # shim py313/PEP696
Params = ParamSpec("Params")
Return = TypeVar("Return")


def context_to_fixture(
    context: Callable[Params, ContextManager[Return]]
) -> Callable[Params, Generator[Return]]:
    @pytest.fixture
    @functools.wraps(context)
    def fixture(
        *args: Params.args, **kwargs: Params.kwargs
    ) -> Generator[Return]:
        with context(*args, **kwargs) as result:
            yield result

    return fixture
