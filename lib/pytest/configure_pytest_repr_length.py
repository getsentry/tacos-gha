"""Nasty hack: pytest's default ellipsizing behavior varies with verbosity"""
# mypy: disable_error_code="attr-defined"

from __future__ import annotations

import pytest

from lib.types import Generator


def configure_pytest_repr_length(
    pytestconfig: pytest.Config,
) -> Generator[None]:
    verbose = pytestconfig.getoption("verbose")
    assert isinstance(verbose, int), verbose

    def saferepr(
        obj: object, maxsize: int | None = None, use_ascii: bool = False
    ) -> str:
        if maxsize is None:
            maxsize = module.DEFAULT_REPR_MAX_SIZE * (verbose + 1)
        return old[1](obj, maxsize=maxsize, use_ascii=use_ascii)

    from _pytest._code import code
    from _pytest._io import saferepr as module

    old = (module.saferepr, code.saferepr)
    (module.saferepr, code.saferepr) = (saferepr, saferepr)

    yield
    (module.saferepr, code.saferepr) = old
