#!/usr/bin/env py.test
from __future__ import annotations

from datetime import datetime

from lib.functions import now
from manual_tests.lib import gha
from manual_tests.lib import slice
from manual_tests.lib import tacos_demo

PLAN_MESSAGE = (
    '<summary>Execution result of "run-all plan -out plan" in "."</summary>'
)


def assert_gha_plan(pr: tacos_demo.PR, since: datetime) -> None:
    gha.assert_eventual_success(pr, "terraform_plan", since)
    assert any(PLAN_MESSAGE in comment for comment in pr.comments(since))


def test(pr: tacos_demo.PR, test_name: str, slices: slice.Slices) -> None:
    assert_gha_plan(pr, pr.since)

    since = now()
    tacos_demo.commit_changes_to(slices, test_name, commit="more code")
    assert_gha_plan(pr, since)
