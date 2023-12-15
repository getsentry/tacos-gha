#!/usr/bin/env py.test
from __future__ import annotations

from datetime import datetime

from lib.functions import now
from manual_tests.lib import tacos_demo
from manual_tests.lib.gh import gh
from manual_tests.lib.slice import Slices

PLAN_MESSAGE = (
    '<summary>Execution result of "run-all plan -out plan" in "."</summary>'
)


def assert_gha_plan(pr: tacos_demo.PR, since: datetime) -> None:
    assert pr.check("terraform_plan").wait(since).success
    assert any(PLAN_MESSAGE in comment for comment in pr.comments(since))


def test(pr: tacos_demo.PR, test_name: str, slices: Slices) -> None:
    assert_gha_plan(pr, pr.since)

    branch, message = tacos_demo.edit(slices, test_name, message="more code")

    since = now()
    gh.commit_and_push(slices.workdir, branch, message)
    assert_gha_plan(pr, since)
    # TODO: assert the plan is what we expect
