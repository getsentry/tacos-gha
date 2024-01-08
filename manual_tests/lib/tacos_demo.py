#!/usr/bin/env py.test
from __future__ import annotations

import typing
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator
from typing import Self
from typing import TypeVar

from lib.constants import NOW
from lib.constants import USER
from lib.functions import one
from lib.sh import sh
from manual_tests.lib.gh import gh
from manual_tests.lib.slice import Slices

# TODO: centralize reused type aliases
Yields = Iterator
T = TypeVar("T")
Generator = typing.Generator[T, None, None]  # shim py313/PEP696
# FIXME: use a more specific type than str
URL = str

# FIXME: we need a better way to demarcate tf-plan in comments
PLAN_MESSAGE = """\
<details>
<summary>Execution result of "run-all plan" in "."</summary>

```terraform
"""


@dataclass(frozen=True)
class PR(gh.PR):
    slices: Slices

    @classmethod
    def from_pr(cls, pr: gh.PR, slices: Slices) -> Self:
        return cls(**vars(pr), slices=slices)

    @classmethod
    def for_slices(
        cls,
        slices: Slices,
        test_name: str,
        branch: object = None,
        message: object = None,
        draft: bool = False,
    ) -> Self:
        workdir = slices.workdir
        branch, message = edit(slices, test_name, branch, message)
        gh.commit_and_push(workdir, branch, message)

        pr = cls.open(workdir, branch, slices=slices, draft=draft)

        sh.banner("PR opened:", pr.url)

        return pr

    @classmethod
    @contextmanager
    def opened_for_slices(
        cls,
        slices: Slices,
        test_name: str,
        branch: gh.Branch = None,
        message: gh.Message = None,
        draft: bool = False,
    ) -> Generator[Self]:
        with sh.cd(slices.workdir):
            pr = cls.for_slices(slices, test_name, branch, message, draft)
            yield pr
            pr.close()

    def get_plan(self, since: datetime | None = None) -> str:
        """Return the body of the github PR comment containing the tf plan."""
        if since is None:
            since = self.since

        assert self.check("Terraform Plan").wait(since).success
        plan = [
            comment
            for comment in self.comments(since)
            if comment.startswith(PLAN_MESSAGE)
        ]
        # there should be just one plan in that timeframe
        return one(plan)


def edit(
    slices: Slices,
    test_name: str,
    branch: gh.Branch = None,
    message: gh.Message = None,
) -> tuple[gh.Branch, gh.Message]:
    if branch:
        branch = f"/{branch}"
    else:
        branch = ""

    branch = (
        f"test/{USER}/{NOW.isoformat().replace(':', '_')}/{test_name}{branch}"
    )

    if message:
        message = f" - {message}"
    else:
        message = ""
    message = f"test: {test_name} ({NOW}){message}"

    # NB: setting an upstream tracking branch makes `gh pr` stop working well
    sh.run(("git", "checkout", "-B", branch))

    slices.edit()
    return branch, message
