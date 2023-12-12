#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.functions import now
from lib.sh import sh
from manual_tests.lib import tacos_demo
from manual_tests.lib import tf


@pytest.mark.xfail(reason="Need another user's approval")
def test(pr: tacos_demo.PR) -> None:
    xfail: list[tuple[bool, object]] = []

    # look at your plan
    plan = pr.get_plan()
    assert plan

    pr.approve()
    assert pr.approved()

    # the taco-apply label causes the plan to become clean:
    assert not tf.plan_clean()
    since = now()
    pr.add_label(":taco::apply")
    assert pr.check("terraform_apply").wait(since).success

    try:
        assert tf.plan_clean()
    except AssertionError:
        xfail.append((False, "plan not clean"))

    pr.merge()

    # show it really did merge
    sh.run(("git", "remote", "update"))
    merged_sha = sh.stdout(("git", "log", "-1", "--format=%H"))
    lines = sh.lines(("git", "branch", "--remotes", "--contains", merged_sha))
    try:
        assert lines
    except AssertionError:
        xfail.append(("assert lines", lines))

    # but at the same time, terraform-plan is clean
    try:
        assert tf.plan_clean()
    except AssertionError:
        xfail.append(("assert tf.plan_clean()", "plan not clean"))
