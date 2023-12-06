#!/usr/bin/env py.test
from __future__ import annotations

from lib.functions import now
from manual_tests.lib import gha
from manual_tests.lib import slice
from manual_tests.lib import tacos_demo
from manual_tests.lib import tf

TEST_NAME = __name__

Branch = int


def test() -> None:
    with tacos_demo.TacosDemoPR.opened_for_test(
        TEST_NAME, slice.random()
    ) as pr:
        gha.assert_eventual_success(pr, "terraform_lock")

        pr.approve()
        assert pr.approved()

        # the taco-apply label causes the plan to become clean:
        assert not tf.plan_clean()
        since = now()
        pr.add_label(":taco::apply")
        gha.assert_eventual_success(pr, "terraform_apply", since)
        assert tf.plan_clean()
