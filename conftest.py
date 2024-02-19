"""Universally-applicable pytest fixtures."""

from __future__ import annotations

import contextlib

import pytest
from pytest import fixture

import lib.pytest.configure_pytest_repr_length
import lib.pytest.doctest
import lib.pytest.hook
from lib.constants import TACOS_GHA_HOME
from lib.sh import sh
from lib.types import Environ
from lib.types import Generator
from lib.types import OSPath

TEST_HOME = TACOS_GHA_HOME / "spec"


@fixture
def user() -> str:
    from lib.constants import USER

    return USER


configure_pytest_repr_length = fixture(
    lib.pytest.configure_pytest_repr_length.configure_pytest_repr_length,
    autouse=True,
    scope="session",
)


@contextlib.contextmanager
def _environ_fixture(environ: Environ) -> Generator[Environ]:
    orig = dict(environ)

    yield environ

    for var in set(orig).union(environ):
        if var in orig:
            environ[var] = orig[var]
        else:
            del environ[var]


@fixture(scope="session")
def session_environ() -> Generator[Environ]:
    """prevent cross-test pollution of environ"""
    import os

    with _environ_fixture(os.environ) as session_environ:
        yield session_environ


@fixture
def environ(session_environ: Environ) -> Generator[Environ]:
    """prevent cross-test pollution of environ"""
    with _environ_fixture(session_environ) as environ:
        yield environ


@fixture
def test_name(request: pytest.FixtureRequest) -> str:
    assert isinstance(
        request.node, pytest.Item  # pyright:ignore[reportUnknownMemberType]
    )
    module_path = request.node.path  # absolute path to the test's module file

    result = module_path.with_suffix("").relative_to(TEST_HOME)
    return str(result).replace("/", "-")


@fixture
def cwd(tmp_path: OSPath, environ: Environ) -> Generator[OSPath]:
    """prevent cross-test pollution of cwd"""
    with sh.cd(tmp_path, environ, direnv=False):
        yield tmp_path


@fixture
def home(cwd: OSPath, environ: Environ) -> Generator[tuple[OSPath, OSPath]]:
    home = cwd / "home"
    orig_home = OSPath(environ["HOME"])
    environ["HOME"] = str(home)

    yield orig_home, home

    environ["HOME"] = str(orig_home)


@fixture()
def xdg_environ(cwd: OSPath, environ: Environ) -> None:
    """Configure XDG so files are written to / read from cwd by default.

    reference:
        https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
    """
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
        xdg_val = cwd / xdg_var
        xdg_val.mkdir()
        environ[xdg_var] = str(xdg_val)


pytest_configure = lib.pytest.doctest.pytest_configure
pytest_unconfigure = lib.pytest.doctest.pytest_unconfigure
