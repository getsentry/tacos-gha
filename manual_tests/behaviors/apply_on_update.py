#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.functions import now
from manual_tests.lib import slice
from manual_tests.lib import tacos_demo
from manual_tests.lib import tf

TEST_NAME = __name__

Branch = int


@pytest.mark.xfail(reason="apply not yet implemented")
def test() -> None:
    with tacos_demo.PR.opened_for_test(TEST_NAME, slice.random()) as pr:
        assert pr.check("terraform_lock").wait().success

        pr.approve()
        assert pr.approved()

        # the taco-apply label causes the plan to become clean:
        assert not tf.plan_clean()
        since = now()
        pr.add_label(":taco::apply")
        assert pr.check("terraform_apply").wait(since).success
        assert tf.plan_clean()
