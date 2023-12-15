#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from manual_tests.lib import tacos_demo
from manual_tests.lib.gh import gh
from manual_tests.lib.slice import Slices
from manual_tests.lib.xfail import XFailed


# reason="locking not yet implemented"
@pytest.mark.xfail(raises=XFailed)
def test(test_name: str, slices: Slices) -> None:
    with (
        tacos_demo.PR.opened_for_slices(slices, test_name, branch=1) as pr1,
        tacos_demo.PR.opened_for_slices(slices, test_name, branch=2) as pr2,
    ):
        checks: dict[tacos_demo.PR, gh.CheckRun] = {
            pr1: pr1.check("terraform_lock").wait(),
            pr2: pr2.check("terraform_lock").wait(),
        }

        for pr, check in checks.items():
            message = "TODO: add comment about lock failure here"
            comments = pr.comments(since=check.startedAt)
            if check.conclusion == "SUCCESS":
                assert message not in comments
            elif check.conclusion == "FAILURE":
                assert message in comments
            else:
                raise AssertionError(check)

        assert {check.conclusion for check in checks.values()} == {
            "SUCCESS",
            "FAILURE",
        }
