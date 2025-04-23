#!/usr/bin/env py.test
from __future__ import annotations

from typing import Callable

from pytest import fixture

from spec.lib import tacos_demo
from spec.lib.slice import Slices


@fixture
def slices_cleanup() -> Callable[[Slices], None]:
    return Slices.force_clean


def test(pr: tacos_demo.PR) -> None:
    # No approval here
    assert pr.check("Required check").wait().success

    # the taco-apply label causes the plan to become clean (and locked):
    assert not pr.slices.plan_is_clean()

    since = pr.add_label(":taco::apply")
    assert pr.check("Terraform Apply").wait(since).failure
    assert pr.slices.plan_is_clean()
    pr.slices.assert_locked()
