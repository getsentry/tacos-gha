#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from manual_tests.lib import gh
from manual_tests.lib import gha
from manual_tests.lib import slice
from manual_tests.lib.tacos_demo import PR


@pytest.mark.xfail(reason="locking not yet implemented")
def test(test_name: str, slices: slice.Slices) -> None:
    with (
        PR.opened_for_test(test_name, slices, branch=1) as pr1,
        PR.opened_for_test(test_name, slices, branch=2) as pr2,
    ):
        checks: dict[gh.PR, gha.Check] = {
            pr1: gha.wait_for_check(pr1, "terraform_lock", pr1.since),
            pr2: gha.wait_for_check(pr2, "terraform_lock", pr2.since),
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
