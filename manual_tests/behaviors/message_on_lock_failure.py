#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from manual_tests.lib import tacos_demo
from manual_tests.lib.gh import gh
from manual_tests.lib.slice import Slices
from manual_tests.lib.xfail import XFailed

MESSAGE = "lock failed, on slice prod/slice-3-vm, due to user1, PR #334 "


# reason="locking not yet implemented"
@pytest.mark.xfail(raises=XFailed)
def test(
    test_name: str, slices: Slices, demo: gh.LocalRepo, tacos_branch: gh.Branch
) -> None:
    with (
        tacos_demo.PR.opened_for_slices(
            slices, test_name, demo, tacos_branch, branch=1
        ) as pr1,
        tacos_demo.PR.opened_for_slices(
            slices, test_name, demo, tacos_branch, branch=2
        ) as pr2,
    ):
        checks: dict[tacos_demo.PR, gh.CheckRun] = {
            pr1: pr1.check("Terraform Lock").wait(),
            pr2: pr2.check("Terraform Lock").wait(),
        }

        for pr, check in checks.items():
            comments = pr.comments(since=check.started)
            if check.conclusion == "SUCCESS":
                assert MESSAGE not in comments
            elif check.conclusion == "FAILURE":
                assert MESSAGE in comments
            else:
                raise AssertionError(check)

        try:
            assert {check.conclusion for check in checks.values()} == {
                "SUCCESS",
                "FAILURE",
            }
        except AssertionError:
            assert {check.conclusion for check in checks.values()} == {
                "SUCCESS"
            }
            raise XFailed("locking not yet implemented")
