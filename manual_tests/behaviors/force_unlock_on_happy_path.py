#!/usr/bin/env py.test
from __future__ import annotations

import pytest
import re

from manual_tests.lib import tacos_demo
from manual_tests.lib.gh import gh
from manual_tests.lib.xfail import XFailed

TEST_NAME = __name__


def assert_slices_unlocked_in_comment(slices: tacos_demo.Slices, comment: str, git_clone: gh.repo.Local) -> None:
    for s in slices:
        slice_path = (slices.workdir / s).relative_to(git_clone.path)
        already_unlocked = re.search(f"success: already unlocked: {slice_path}", comment) is not None
        lock_released = re.search(f"success: released lock \(from .+\): {slice_path}", comment) is not None
        assert already_unlocked or lock_released, f"slice {slice_path} not unlocked"


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
    assert pr.check("Summarize lock state.").wait(since).success
    comments = pr.comments(since=since)

    # Find the terraform lock state comment
    lock_state_comment = None
    for comment in comments:
        if "Terraform lock state:" in comment:
            lock_state_comment = comment
            break

    assert lock_state_comment is not None, "Terraform lock state comment not found"

    assert_slices_unlocked_in_comment(
        slices, comment, git_clone
    )
