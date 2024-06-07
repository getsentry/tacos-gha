"""Universally-applicable pytest fixtures."""

from __future__ import annotations

import pytest
from pytest import fixture

import lib.pytest.doctest
import lib.pytest.hook
import lib.pytest.plugin.cap1fd
import lib.pytest.plugin.collectonly_json
import lib.pytest.plugin.pytest_repr_length
from lib import env
from lib.constants import TACOS_GHA_HOME
from lib.env import Environ
from lib.sh import sh
from lib.types import Generator
from lib.types import OSPath
from lib.types import Path

pytest_plugins = (
    # they insist on strings =.=
    lib.pytest.plugin.cap1fd.__name__,
    lib.pytest.plugin.collectonly_json.__name__,
    lib.pytest.plugin.pytest_repr_length.__name__,
)


@fixture
def user() -> str:
    from lib.constants import USER

    return USER


@fixture(scope="session")
def session_environ() -> Generator[Environ]:
    """prevent cross-test pollution of environ"""
    from os import environ

    with env.fixed(environ) as session_environ:
        yield session_environ


@fixture
def environ(session_environ: Environ) -> Generator[Environ]:
    """prevent cross-test pollution of environ"""
    with env.fixed(session_environ) as environ:
        yield environ


@fixture
def test_path(request: pytest.FixtureRequest) -> Path:
    assert isinstance(
        request.node, pytest.Item  # pyright:ignore[reportUnknownMemberType]
    )
    # absolute path to the test's module file
    module_path = Path(request.node.path)
    return module_path.relative_to(TACOS_GHA_HOME)


@fixture
def test_name(test_path: Path) -> str:
    result = test_path.with_suffix("").relative_to("spec")
    return str(result).replace("/", "-")


@fixture
def cwd(tmp_path: OSPath, environ: Environ) -> Generator[OSPath]:
    """prevent cross-test pollution of cwd"""
    with sh.cd(tmp_path, environ, direnv=False):
        yield tmp_path


@fixture
def home(cwd: OSPath, environ: Environ) -> Generator[tuple[OSPath, OSPath]]:
    orig_home = environ["HOME"]

    home = cwd / "home"
    home.mkdir()
    environ["HOME"] = str(home)

    yield OSPath(orig_home), home

    environ["HOME"] = orig_home


@fixture
def xdg_environ(cwd: OSPath, environ: Environ) -> Generator[Environ]:
    """Configure XDG so files are written to / read from cwd by default.

    reference:
        https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
    """
    with env.fixed(environ) as xdg_environ:
        for xdg_var in (
            "CACHE_HOME",
            "CONFIG_HOME",
            "DATA_HOME",
            "STATE_HOME",
            "RUNTIME_DIR",
            "CONFIG_DIRS",
            "DATA_DIRS",
        ):
            xdg_val = cwd / xdg_var.lower()
            xdg_val.mkdir()
            xdg_environ["XDG_" + xdg_var] = str(xdg_val)

        yield xdg_environ


pytest_configure = lib.pytest.doctest.pytest_configure
pytest_unconfigure = lib.pytest.doctest.pytest_unconfigure
