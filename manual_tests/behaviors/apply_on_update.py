#!/usr/bin/env py.test
from __future__ import annotations

from lib.types import OSPath
from manual_tests.lib import tacos_demo
from manual_tests.lib import tf

TEST_NAME = __name__


def assert_locked(pr: tacos_demo.PR) -> None:
    lock_run = pr.check(
        "Terraform Lock", "tacos-gha / Determine TF slices to lock"
    ).wait()
    assert lock_run.success
    for slice in pr.slices:
        assert (
            pr.check("Terraform Lock", f"tacos-gha / main ({slice})")
            .wait(since=lock_run.completed, timeout=10)
            .success
        )


def test(pr: tacos_demo.PR, workdir: OSPath) -> None:
    assert_locked(pr)

    pr.approve()
    assert pr.approved()

    # the taco-apply label causes the plan to become clean:
    assert tf.plan_dirty(workdir)
    since = pr.add_label(":taco::apply")
    assert pr.check("Terraform Apply").wait(since).success
    assert tf.plan_clean(workdir)
