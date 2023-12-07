#!/usr/bin/env py.test
from __future__ import annotations

from lib.functions import now
from manual_tests.lib import gha
from manual_tests.lib import slice
from manual_tests.lib import tacos_demo

TEST_NAME = __name__


def test() -> None:
    slices = slice.random()

    since = now()
    tacos_demo.clone()
    tacos_demo_pr = tacos_demo.PR.for_test(TEST_NAME, slices)
    try:
        gha.assert_eventual_success(tacos_demo_pr, "terraform_lock", since)
        since = now()
        tacos_demo_pr.approve()
        assert tacos_demo_pr.approved()
        tacos_demo_pr.add_label(":taco::apply")
        gha.assert_eventual_success(tacos_demo_pr, "terraform_apply", since)
        since = now()
        tacos_demo_pr.merge_pr()
    except Exception:  # If we manage to merge, we don't need to close.
        tacos_demo_pr.close()
        raise
    gha.assert_eventual_success(tacos_demo_pr, "terraform_unlock", since)
