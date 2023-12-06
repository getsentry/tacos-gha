from __future__ import annotations

import typing
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator
from typing import Self
from typing import TypeVar

from lib import sh
from lib.constants import NOW
from lib.constants import USER
from manual_tests.lib import gh
from manual_tests.lib import slice

# TODO: centralize reused type aliases
Yields = Iterator
T = TypeVar("T")
Generator = typing.Generator[T, None, None]  # shim py313/PEP696
# FIXME: use a more specific type than str
Branch = str
URL = str


@dataclass(frozen=True)
class TacosDemoPR(gh.PR):
    slices: slice.Slices

    @classmethod
    def from_pr(cls, pr: gh.PR, slices: slice.Slices) -> Self:
        return cls(**vars(pr), slices=slices)

    @classmethod
    def for_test(cls, test_name: str, slices: slice.Slices) -> Self:
        branch = commit_changes_to(slices, test_name)

        pr = cls.open(branch, slices=slices)

        sh.banner("PR opened:", pr.url)

        return pr

    @classmethod
    @contextmanager
    def opened_for_test(
        cls, test_name: str, slices: slice.Slices
    ) -> Generator[Self]:
        clone()
        tacos_demo_pr = cls.for_test(test_name, slices)
        yield tacos_demo_pr
        tacos_demo_pr.close()


def clone() -> None:
    sh.run(("rm", "-rf", "tacos-demo"))
    sh.run(("git", "clone", "git@github.com:getsentry/tacos-demo"))
    sh.cd("tacos-demo/terraform/env/prod/")


def commit_changes_to(
    slices: slice.Slices, test_name: str, postfix: str = ""
) -> Branch:
    branch = f"test/{USER}/{test_name}/{NOW.isoformat().replace(':', '_')}"

    # NB: setting an upstream tracking branch makes `gh pr` stop working well
    sh.run(("git", "checkout", "-B", branch))

    for s in slices:
        slice.edit(s)
    if postfix:
        postfix = " - " + postfix

    sh.run(("git", "commit", "-m", f"test: {test_name} ({NOW}){postfix}"))
    sh.run(("git", "push", "origin", f"{branch}:{branch}"))

    return branch
