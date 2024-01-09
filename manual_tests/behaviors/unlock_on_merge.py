#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from manual_tests.lib import tacos_demo
from manual_tests.lib.xfail import XFailed

TEST_NAME = __name__


def assert_locked(pr: tacos_demo.PR) -> None:
    lock_run = pr.check(
        "Terraform Lock", "tacos-gha / Determine TF slices to lock"
    ).wait()
    assert lock_run.success
    for slice in pr.slices:
        assert (
            pr.check("Terraform Lock", f"tacos-gha / main ({slice})")
            .wait(since=lock_run.completed, timeout=30)
            .success
        )


@pytest.mark.xfail(raises=XFailed)
def test(pr: tacos_demo.PR) -> None:
    # TODO: use slice name
    assert_locked(pr)

    since = pr.approve()
    assert pr.approved()

    pr.merge()

    try:
        assert pr.check("Terraform Unlock").wait(since, timeout=6).success
    except AssertionError:
        raise XFailed("Unlock not yet implemented.")
