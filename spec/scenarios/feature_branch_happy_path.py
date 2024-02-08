#!/usr/bin/env py.test
from __future__ import annotations

from lib.sh import sh
from spec.lib import tacos_demo
from spec.lib.gh import gh


def apply(pr: tacos_demo.PR) -> None:
    # the taco-apply label causes the plan to become clean:
    assert not pr.slices.plan_is_clean()
    since = pr.add_label(":taco::apply")
    assert pr.check("Terraform Apply").wait(since).success

    assert pr.slices.plan_is_clean()


def assert_merged() -> None:
    sh.run(("git", "remote", "update"))
    merged_sha = sh.stdout(("git", "log", "-1", "--format=%H"))
    lines = sh.lines(("git", "branch", "--remotes", "--contains", merged_sha))
    assert lines


def test(pr: tacos_demo.PR) -> None:
    sh.banner("look at your plan")
    plan = pr.get_plans()
    assert plan

    sh.banner("apply")
    pr.approve()  # needs at least one approval
    assert pr.is_approved()
    apply(pr)

    sh.banner("edit, more")
    slices = pr.slices.with_some_overlap()
    slices.edit()
    pr = pr.with_slices(slices)

    gh.commit_and_push(pr.branch, "more changes")

    sh.banner("apply, again")
    apply(pr)

    sh.banner("merge")
    pr.merge()

    sh.banner("show it really did merge")
    assert_merged()

    sh.banner("show terraform-plan really is clean")
    assert pr.slices.plan_is_clean()
