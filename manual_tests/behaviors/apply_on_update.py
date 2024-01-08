#!/usr/bin/env py.test
from __future__ import annotations

from pathlib import Path

from manual_tests.lib import tacos_demo
from manual_tests.lib import tf

TEST_NAME = __name__


def test(pr: tacos_demo.PR, workdir: Path) -> None:
    # TODO: use slice name
    assert pr.check("Terraform Lock", "tacos-gha / main").wait().success

    pr.approve()
    assert pr.approved()

    # the taco-apply label causes the plan to become clean:
    assert tf.plan_dirty(workdir)
    since = pr.add_label(":taco::apply")
    assert pr.check("Terraform Apply", "tacos-gha / main").wait(since).success
    assert tf.plan_clean(workdir)
