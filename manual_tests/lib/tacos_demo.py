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
from manual_tests.lib import slice
from manual_tests.lib.gh import gh

# TODO: centralize reused type aliases
Yields = Iterator
T = TypeVar("T")
Generator = typing.Generator[T, None, None]  # shim py313/PEP696
# FIXME: use a more specific type than str
Branch = str
URL = str


@dataclass(frozen=True)
class PR(gh.PR):
    slices: slice.Slices

    @classmethod
    def from_pr(cls, pr: gh.PR, slices: slice.Slices) -> Self:
        return cls(**vars(pr), slices=slices)

    @classmethod
    def for_test(
        cls, test_name: str, slices: slice.Slices, branch: object = None
    ) -> Self:
        branch = commit_changes_to(slices, test_name, branch=branch)

        pr = cls.open(branch, slices=slices)

        sh.banner("PR opened:", pr.url)

        return pr

    @classmethod
    @contextmanager
    def opened_for_test(
        cls, test_name: str, slices: slice.Slices, branch: object = None
    ) -> Generator[Self]:
        clone()
        tacos_demo_pr = cls.for_test(test_name, slices, branch)
        with sh.cd(Path("tacos-demo/terraform/env/prod/")):
            yield tacos_demo_pr
        tacos_demo_pr.close()


def clone() -> None:
    sh.run(("rm", "-rf", "tacos-demo"))
    sh.run(("git", "clone", "git@github.com:getsentry/tacos-demo"))


def commit_changes_to(
    slices: slice.Slices,
    test_name: str,
    commit: str = "",
    branch: object = None,
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

    for s in slices:
        slice.edit(s)

    if commit:
        commit = " - " + commit
    sh.run(("git", "commit", "-m", f"test: {test_name} ({NOW}){commit}"))
    sh.run(("git", "push", "origin", f"{branch}:{branch}"))

    return branch
