"""pytest fixtures specific to tacos-gha demo"""
from __future__ import annotations

from pathlib import Path

from pytest import fixture

from lib.sh import sh
from lib.sh.cd import cd
from lib.types import Generator
from manual_tests.lib import tacos_demo
from manual_tests.lib.gh import gh
from manual_tests.lib.slice import Slices


@fixture
def git_remote(user: str) -> gh.repo.Remote:
    return gh.repo.Remote(
        url="git@github.com:getsentry/tacos-demo",
        subpath=Path(f"terraform/env.{user}/prod/"),
    )


@fixture
def git_clone(
    cwd: Path, git_remote: gh.repo.Remote
) -> Generator[gh.repo.Local]:
    with git_remote.cloned(cwd) as clone:
        yield clone


@fixture
def workdir(git_clone: gh.repo.Local) -> Generator[Path]:
    with cd(git_clone.workdir):
        yield git_clone.workdir


@fixture
def slices(workdir: Path) -> Slices:
    slices = Slices.from_path(workdir)
    return slices.random()


@fixture
def pr(slices: Slices, test_name: str) -> Generator[tacos_demo.PR]:
    with tacos_demo.PR.opened_for_slices(slices, test_name) as pr:
        yield pr


GCLOUD_CONFIG = Path(".config/gcloud/configurations")


# TODO: convert to `gcloud` fixture, setting GCLOUD_AUTH_TOKEN
@fixture
def home(home: tuple[Path, Path]) -> tuple[Path, Path]:
    old, new = home

    # let gcloud see its config still, though
    # it doesn't respect XDG, apparently
    src = old / GCLOUD_CONFIG
    dst = new / GCLOUD_CONFIG

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.symlink_to(src)

    return home


# TODO: refactor gh module to take token as an argument
@fixture(autouse=True, scope="session")
def gh_token() -> None:
    from os import environ

    environ["GH_TOKEN"] = sh.stdout(("gh", "auth", "token"))
