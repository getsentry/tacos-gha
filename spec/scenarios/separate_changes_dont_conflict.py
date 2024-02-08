#!/usr/bin/env py.test
from __future__ import annotations

from lib.sh import sh
from spec.lib import tacos_demo
from spec.lib.gh import gh
from spec.lib.slice import Slices


def test(
    test_name: str, demo: gh.LocalRepo, tacos_branch: gh.Branch, slices: Slices
) -> None:
    sh.banner(f"User 1 opens a PR for some slices")
    slices1 = slices
    print(slices1)

    sh.banner(f"User 2 opens a PR for separate slices")
    slices2 = (slices.all - slices1).random()
    print(slices2)

    with (
        tacos_demo.PR.opened_for_slices(
            slices, test_name, demo, tacos_branch, 1
        ) as pr1,
        tacos_demo.PR.opened_for_slices(
            slices2, test_name, demo, tacos_branch, 2
        ) as pr2,
    ):
        sh.banner("User 1 acquires the lock")
        assert pr1.check("Terraform Plan").wait().success

        sh.banner("User 2 acquires the lock")
        assert pr2.check("Terraform Plan").wait().success
