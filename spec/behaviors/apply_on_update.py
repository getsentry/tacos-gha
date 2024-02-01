#!/usr/bin/env py.test
from __future__ import annotations

from typing import Callable

from spec.lib import tacos_demo
from spec.lib.slice import Slices

TEST_NAME = __name__

from pytest import fixture


@fixture
def slices_cleanup() -> Callable[[Slices], None]:
    return Slices.force_clean


def test(pr: tacos_demo.PR) -> None:
    pr.approve()
    assert pr.is_approved()

    # the taco-apply label causes the plan to become clean:
    assert not pr.slices.plan_is_clean()
    since = pr.add_label(":taco::apply")
    assert pr.check("Terraform Apply").wait(since).success
    assert pr.slices.plan_is_clean()
