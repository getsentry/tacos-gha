#!/usr/bin/env py.test
from __future__ import annotations

from manual_tests.lib import tacos_demo
from manual_tests.lib import tf
from manual_tests.lib.slice import Slices

TEST_NAME = __name__


def test(pr: tacos_demo.PR, clean_slices: Slices) -> None:
    pr.approve()
    assert pr.approved()

    # the taco-apply label causes the plan to become clean:
    assert tf.plan_is_dirty(clean_slices.path)
    since = pr.add_label(":taco::apply")
    assert pr.check("Terraform Apply").wait(since).success
    assert tf.plan_is_clean(clean_slices.path)
