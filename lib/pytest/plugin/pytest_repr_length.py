"""Nasty hack: pytest's default ellipsizing behavior varies with verbosity"""

from __future__ import annotations

import pytest

from lib.types import Generator

# mypy: disable_error_code="attr-defined"
# error: Module "_pytest._code.code" does not explicitly export attribute "saferepr"


# TODO: I was forced to typo the name to avoid a "unknown hook" error
# TODO: figure out a sane way to export this as a contextmanager, too
@pytest.fixture(autouse=True, scope="session")
def pyytest_repr_length(pytestconfig: pytest.Config) -> Generator[int]:
    verbose = pytestconfig.getoption("verbose")
    assert isinstance(verbose, int), verbose

    from _pytest._code import code
    from _pytest._io import saferepr as module

    new_maxsize = module.DEFAULT_REPR_MAX_SIZE * (2**verbose)

    def saferepr(
        obj: object, maxsize: int | None = None, use_ascii: bool = False
    ) -> str:
        if maxsize is None:
            maxsize = new_maxsize
        return old[1](obj, maxsize=maxsize, use_ascii=use_ascii)

    # TODO: make use of lib.patch, to replace ad-hoc monkeypatching
    old = (module.saferepr, code.saferepr)
    (module.saferepr, code.saferepr) = (saferepr, saferepr)

    yield new_maxsize
    (module.saferepr, code.saferepr) = old
