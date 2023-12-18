#!/usr/bin/env py.test
from __future__ import annotations

from manual_tests.lib import tacos_demo
from manual_tests.lib.gh import gh
from manual_tests.lib.slice import Slices


def test(pr: tacos_demo.PR, test_name: str, slices: Slices) -> None:
    assert pr.get_plan()

    branch, message = tacos_demo.edit(slices, test_name, message="more code")

    gh.commit_and_push(slices.workdir, branch, message)
    assert pr.get_plan()
    # TODO: assert the plan is what we expect
