#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.sh import sh
from manual_tests.lib import tacos_demo
from manual_tests.lib import tf
from manual_tests.lib.gh import gh
from manual_tests.lib.slice import Slices
from manual_tests.lib.xfail import XFailed
from manual_tests.lib.xfail import XFails


def apply(pr: tacos_demo.PR, xfails: XFails) -> None:
    # the taco-apply label causes the plan to become clean:
    assert tf.plan_dirty(pr.slices.workdir)
    since = pr.add_label(":taco::apply")
    assert pr.check("Terraform Apply", "tacos-gha / main").wait(since).success

    try:
        assert tf.plan_clean(pr.slices.workdir)
    except AssertionError:
        xfails.append(("assert tf.plan_clean()", "plan not clean"))


def assert_merged(xfails: XFails) -> None:
    sh.run(("git", "remote", "update"))
    merged_sha = sh.stdout(("git", "log", "-1", "--format=%H"))
    lines = sh.lines(("git", "branch", "--remotes", "--contains", merged_sha))
    try:
        assert lines
    except AssertionError:
        xfails.append(("assert lines", lines))


@pytest.mark.xfail(raises=XFailed)
def test(pr: tacos_demo.PR) -> None:
    xfails: XFails = []

    sh.banner("look at your plan")
    plan = pr.get_plan()
    assert plan

    sh.banner("apply")
    pr.approve()  # needs at least one approval
    assert pr.approved()
    apply(pr, xfails)

    sh.banner("edit, more")
    slices = Slices.from_path(pr.slices.workdir).random()
    slices.edit()
    gh.commit_and_push(slices.workdir, pr.branch, "more changes")

    sh.banner("apply, again")
    apply(pr, xfails)

    sh.banner("merge")
    pr.merge()

    sh.banner("show it really did merge")
    assert_merged(xfails)

    sh.banner("show terraform-plan really is clean")
    try:
        assert tf.plan_clean(pr.slices.workdir)
    except AssertionError:
        xfails.append(("assert tf.plan_clean()", "plan not clean"))

    if xfails:
        raise XFailed(str(xfails))
