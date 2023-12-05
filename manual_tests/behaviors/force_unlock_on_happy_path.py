#!/usr/bin/env py.test
from __future__ import annotations

from lib.functions import now
from manual_tests.lib import gh
from manual_tests.lib import gha
from manual_tests.lib import slice
from manual_tests.lib import tacos_demo

TEST_NAME = __name__


def test() -> None:
    tacos_demo.clone()

    since = now()
    tacos_demo_pr = tacos_demo.new_pr(TEST_NAME, slice.random())
    try:
        gha.assert_eventual_success("terraform_lock", since)
        gh.add_label(tacos_demo_pr.url, ":taco::unlock")
        gha.assert_eventual_success("terraform_unlock", since)
        gh.assert_matching_comment(
            "INFO: Main branch clean, unlock successful.", since
        )
    finally:
        gh.close_pr(tacos_demo_pr.branch)
