#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from manual_tests.lib import tacos_demo
from manual_tests.lib.gh import gh
from manual_tests.lib.xfail import XFailed

TEST_NAME = __name__


@pytest.mark.xfail(raises=XFailed)
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

    since = pr.add_label(":taco::unlock")
    assert pr.check("terraform_unlock").wait(since).success

    try:
        assert "INFO: Main branch clean, unlock successful." in pr.comments(
            since=since
        )
    except AssertionError:
        raise XFailed("still need to post message from unlock")
