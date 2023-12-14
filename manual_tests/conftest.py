"""pytest fixtures specific to tacos-gha demo"""
from __future__ import annotations

from pathlib import Path

from pytest import fixture

from lib.types import Generator
from manual_tests.lib import tacos_demo
from manual_tests.lib.gh import gh
from manual_tests.lib.slice import Slices


@fixture
def user() -> str:
    from lib.constants import USER

    return USER


@fixture
def git_remote(user: str) -> gh.repo.Remote:
    return gh.repo.Remote(
        url="git@github.com:getsentry/tacos-demo",
        subpath=Path(f"tacos-demo/terraform/env.{user}/prod/"),
    )


@fixture
def git_clone(
    cwd: Path, git_remote: gh.repo.Remote
) -> Generator[gh.repo.Local]:
    with git_remote.cloned(cwd) as clone:
        yield clone


@fixture
def slices(git_clone: gh.repo.Local) -> Slices:
    return Slices.from_path(git_clone.workdir).random()


@fixture
def pr(slices: Slices, test_name: str) -> Generator[tacos_demo.PR]:
    with tacos_demo.PR.opened_for_test(slices, test_name) as pr:
        yield pr
