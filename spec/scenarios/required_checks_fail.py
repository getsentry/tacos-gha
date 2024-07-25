#!/usr/bin/env py.test
from __future__ import annotations

from pathlib import Path

from lib.sh import sh
from spec.lib import tacos_demo
from spec.lib.gh import gh
from spec.lib.slice import Slices


def test(
    slices: Slices, test_name: str, demo: gh.LocalRepo, tacos_branch: str
) -> None:
    with tacos_demo.PR.opened_for_slices(
        slices, test_name, demo, tacos_branch
    ) as pr:
        sh.banner("look at your plan")
        plan = pr.get_plans()
        assert plan

        sh.banner("apply")
        pr.approve()
        assert pr.is_approved()

        # Wait for all checks
        pr.check().wait

        print(pr.is_passing_checks())

        assert not pr.slices.plan_is_clean()
        since = pr.add_label(":taco::apply")

        assert pr.check("Terraform Apply").wait(since).failure
        assert "PR has not passed all required checks" in pr.comments(since)
