#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.sh import sh
from spec.lib import tacos_demo
from spec.lib.gh import gh
from spec.lib.slice import Slices
from spec.lib.xfail import XFailed
from spec.lib.xfail import XFails


def apply(pr: tacos_demo.PR, xfails: XFails) -> None:
    # the taco-apply label causes the plan to become clean:
    assert not pr.slices.plan_is_clean()
    since = pr.add_label(":taco::apply")
    assert pr.check("Terraform Apply").wait(since).success

    try:
        assert pr.slices.plan_is_clean()
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
    plan = pr.get_plans()
    assert plan

    sh.banner("apply")
    pr.approve()  # needs at least one approval
    assert pr.is_approved()
    apply(pr, xfails)

    sh.banner("edit, more")
    slices = Slices.from_path(pr.slices.path).random()
    slices.edit()
    gh.commit_and_push(pr.branch, "more changes")

    sh.banner("apply, again")
    apply(pr, xfails)

    sh.banner("merge")
    pr.merge()

    sh.banner("show it really did merge")
    assert_merged(xfails)

    sh.banner("show terraform-plan really is clean")
    try:
        assert pr.slices.plan_is_clean()
    except AssertionError:
        xfails.append(("assert tf.plan_clean()", "plan not clean"))

    if xfails:
        raise XFailed(str(xfails))
