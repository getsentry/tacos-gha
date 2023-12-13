#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.functions import now
from lib.sh import sh
from manual_tests.lib import tacos_demo
from manual_tests.lib import tf
from manual_tests.lib.gh import gh
from manual_tests.lib.slice import Slices
from manual_tests.lib.xfail import XFailed
from manual_tests.lib.xfail import XFails


def apply(pr: gh.PR, xfail: XFails) -> None:
    # the taco-apply label causes the plan to become clean:
    assert not tf.plan_clean()
    since = now()
    pr.add_label(":taco::apply")
    assert pr.check("terraform_apply").wait(since).success

    try:
        assert tf.plan_clean()
    except AssertionError:
        xfail.append(("assert tf.plan_clean()", "plan not clean"))


def assert_merged(xfail: XFails) -> None:
    sh.run(("git", "remote", "update"))
    merged_sha = sh.stdout(("git", "log", "-1", "--format=%H"))
    lines = sh.lines(("git", "branch", "--remotes", "--contains", merged_sha))
    try:
        assert lines
    except AssertionError:
        xfail.append(("assert lines", lines))


@pytest.mark.xfail(reason="apply not yet implemented", raises=XFailed)
def test(pr: tacos_demo.PR, test_name: str) -> None:
    xfail: XFails = []

    sh.banner("look at your plan")
    plan = pr.get_plan()
    assert plan

    sh.banner("apply")
    pr.approve()  # needs at least one approval
    assert pr.approved()
    apply(pr, xfail)

    sh.banner("edit, more")
    tacos_demo.commit_changes_to(Slices.random(), test_name, pr.branch)

    sh.banner("apply, again")
    apply(pr, xfail)

    sh.banner("merge")
    pr.merge()

    sh.banner("show it really did merge")
    assert_merged(xfail)

    sh.banner("show terraform-plan really is clean")
    try:
        assert tf.plan_clean()
    except AssertionError:
        xfail.append(("assert tf.plan_clean()", "plan not clean"))

    if xfail:
        raise XFailed(xfail)
