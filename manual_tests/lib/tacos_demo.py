from __future__ import annotations

import typing
from contextlib import contextmanager
from dataclasses import dataclass
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
URL = str


@dataclass(frozen=True)
class PR(gh.PR):
    slices: Slices

    @contextmanager
    @classmethod
    def opened_for_test(
        cls,
        slices: Slices,
        test_name: str,
        branch: gh.Branch = None,
        message: gh.Message = None,
    ) -> Generator[Self]:
        with gh.PR.opened(
            slices.workdir,
            edit=lambda: edit(slices, test_name, branch, message),
        ) as pr:
            yield cls(**vars(pr), slices=slices)


def edit(
    slices: Slices,
    test_name: str,
    branch: gh.Branch = None,
    message: gh.Message = None,
) -> tuple[gh.Branch, gh.Message]:
    if branch:
        branch = f"/{branch}"

    branch = (
        f"test/{USER}/{NOW.isoformat().replace(':', '_')}/{test_name}{branch}"
    )

    if message:
        message = f" - {message}"
    message = f"test: {test_name} ({NOW}){message}"

    # NB: setting an upstream tracking branch makes `gh pr` stop working well
    sh.run(("git", "checkout", "-B", branch))

    slices.edit()
    return branch, message
