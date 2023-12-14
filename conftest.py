"""Universally-applicable pytest fixtures."""
from __future__ import annotations

from pathlib import Path

import pytest
from pytest import fixture

from lib.sh import sh
from lib.types import Environ
from lib.types import Generator


@fixture
def environ() -> Generator[Environ]:
    """prevent cross-test pollution of environ"""
    from os import environ

    orig = environ.copy()

    yield environ

    for var in set(orig).union(environ):
        if var in orig:
            environ[var] = orig[var]
        else:
            del environ[var]


@fixture
def test_name(request: pytest.FixtureRequest) -> str:
    assert isinstance(
        request.node, pytest.Item  # pyright:ignore[reportUnknownMemberType]
    )
    module_path = request.node.path  # path to the test's module file
    return module_path.with_suffix("").name


@fixture
def cwd(tmp_path: Path, environ: Environ) -> Generator[Path]:
    """prevent cross-test pollution of cwd"""
    with sh.cd(tmp_path, env=environ):
        yield tmp_path


@fixture(autouse=True)
def xdg(cwd: Path, environ: Environ) -> None:
    """Configure XDG so files are written to / read from cwd by default.

    Currently, none of the configured xdg directories are created.

    reference:
        https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
    """
    environ["HOME"] = str(cwd / "home")

    for xdg_var in (
        "CACHE_HOME",
        "CONFIG_HOME",
        "DATA_HOME",
        "STATE_HOME",
        "RUNTIME_DIR",
        "CONFIG_DIRS",
        "DATA_DIRS",
    ):
        xdg_var = "XDG_" + xdg_var
        environ[xdg_var] = str(cwd / xdg_var)
