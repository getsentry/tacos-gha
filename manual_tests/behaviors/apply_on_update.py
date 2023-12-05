#!/usr/bin/env py.test
from __future__ import annotations

from lib.functions import now
from manual_tests.lib import gh
from manual_tests.lib import gha
from manual_tests.lib import slice
from manual_tests.lib import tacos_demo
from manual_tests.lib import tf

TEST_NAME = __name__

Branch = int


def test() -> None:
    tacos_demo.clone()
    tacos_demo_pr = tacos_demo.new_pr(TEST_NAME, slice.random())
    try:
        since = now()
        gha.assert_eventual_success("terraform_lock", since)

        gh.approve_pr(tacos_demo_pr.url)
        gh.assert_pr_is_approved(tacos_demo_pr.url)

        # the taco-apply label causes the plan to become clean:
        assert not tf.plan_clean()
        since = now()
        gh.add_label(tacos_demo_pr.url, ":taco::apply")
        gha.assert_eventual_success("terraform_apply", since)
        assert tf.plan_clean()
    finally:
        gh.close_pr(tacos_demo_pr.branch)
