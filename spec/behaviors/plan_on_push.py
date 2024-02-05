#!/usr/bin/env py.test
from __future__ import annotations

from spec.lib import tacos_demo
from spec.lib.gh import gh
from spec.lib.slice import Slices


def test(
    pr: tacos_demo.PR, test_name: str, slices: Slices, demo: gh.LocalRepo
) -> None:
    branch, message = tacos_demo.edit_slices(
        slices, test_name, message="more code"
    )

    gh.commit_and_push(demo, branch, message)
    plans = pr.get_plans()
    assert plans
    slices_found = set(plans)
    assert slices.slices == slices_found
