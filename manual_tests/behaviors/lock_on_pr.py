#!/usr/bin/env py.test
from __future__ import annotations

from manual_tests.lib import tacos_demo
from manual_tests.lib.gh import gh


def test(pr: tacos_demo.PR, git_clone: gh.repo.Local) -> None:
    slices = pr.slices
    for s in slices:
        assert (
            pr.check(
                f"terraform_lock ({(slices.workdir / s).relative_to(git_clone.path)})"
            )
            .wait()
            .success
        )
    slices.assert_locked()
