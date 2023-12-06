#!/usr/bin/env py.test
from __future__ import annotations

from datetime import datetime

from lib.functions import now
from manual_tests.lib import gha
from manual_tests.lib import slice
from manual_tests.lib import tacos_demo

TEST_NAME = __name__

Branch = int


def assert_gha_plan(pr: tacos_demo.TacosDemoPR, since: datetime) -> None:
    gha.assert_eventual_success(pr, "terraform_plan", since)
    assert "Execution result of" in pr.comments(since)


def test() -> None:
    with tacos_demo.TacosDemoPR.opened_for_test(
        TEST_NAME, slice.random()
    ) as pr:
        assert_gha_plan(pr, pr.since)

        since = now()
        tacos_demo.commit_changes_to(
            slice.random(), TEST_NAME, postfix="more code"
        )
        assert_gha_plan(pr, since)
