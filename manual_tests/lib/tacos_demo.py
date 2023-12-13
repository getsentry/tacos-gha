from __future__ import annotations

import typing
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
from typing import Self
from typing import TypeVar

from lib.constants import NOW
from lib.constants import USER
from lib.sh import sh
from manual_tests.lib.gh import gh
from manual_tests.lib.slice import Slices

# TODO: centralize reused type aliases
Yields = Iterator
T = TypeVar("T")
Generator = typing.Generator[T, None, None]  # shim py313/PEP696
# FIXME: use a more specific type than str
Branch = str
URL = str


@dataclass(frozen=True)
class PR(gh.PR):
    slices: Slices

    @classmethod
    def from_pr(cls, pr: gh.PR, slices: Slices) -> Self:
        return cls(**vars(pr), slices=slices)

    @classmethod
    def for_test(
        cls, test_name: str, slices: Slices, branch: object = None
    ) -> Self:
        branch = commit_changes_to(slices, test_name, branch=branch)

        pr = cls.open(branch, slices=slices)

        sh.banner("PR opened:", pr.url)

        return pr

    @classmethod
    @contextmanager
    def opened_for_test(
        cls, test_name: str, slices: Slices, branch: object = None
    ) -> Generator[Self]:
        clone()
        with sh.cd(Path("tacos-demo/terraform/env/prod/")):
            tacos_demo_pr = cls.for_test(test_name, slices, branch)
            yield tacos_demo_pr
        tacos_demo_pr.close()


def clone(cwd: Path | None = None) -> Path:
    if cwd is None:
        cwd = Path.cwd()

    result = cwd / 'tacos-demo'
    sh.run(("rm", "-rf", result))
    sh.run(("git", "clone", "git@github.com:getsentry/tacos-demo", result))
    retur result
    


def commit(branch: Branch, test_name: str, message: str = "") -> None:
    if message:
        message = " - " + message
    sh.run(("git", "commit", "-m", f"test: {test_name} ({NOW}){message}"))
    sh.run(("git", "push", "origin", f"{branch}:{branch}"))


def commit_changes_to(
    slices: Slices, test_name: str, message: str = "", branch: object = None
) -> Branch:
    if branch is None:
        branch = ""
    else:
        branch = f"/{branch}"

    branch = (
        f"test/{USER}/{NOW.isoformat().replace(':', '_')}/{test_name}{branch}"
    )

    # NB: setting an upstream tracking branch makes `gh pr` stop working well
    sh.run(("git", "checkout", "-B", branch))

    for slice in slices:
        slice.edit()

    commit(branch, test_name, message)

    return branch
