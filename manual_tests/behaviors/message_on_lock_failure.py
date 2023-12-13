#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from manual_tests.lib.gh import gh
from manual_tests.lib.slice import Slices
from manual_tests.lib.tacos_demo import PR


@pytest.mark.xfail(reason="locking not yet implemented")
def test(test_name: str, slices: Slices) -> None:
    with (
        PR.opened_for_test(test_name, slices, branch=1) as pr1,
        PR.opened_for_test(test_name, slices, branch=2) as pr2,
    ):
        checks: dict[gh.PR, gh.CheckRun] = {
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
