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
    random_slice = slice.random()
    tacos_demo_pr1 = tacos_demo.new_pr(f"{TEST_NAME}-1", random_slice)
    gh.checkout("main")
    tacos_demo_pr2 = tacos_demo.new_pr(f"{TEST_NAME}-2", random_slice)
    try:
        gh.checkout(tacos_demo_pr1.branch)
        check_1 = gha.wait_for_check("terraform_lock", since)
        gh.checkout(tacos_demo_pr2.branch)
        check_2 = gha.wait_for_check("terraform_lock", since)
        is_check_1_success = check_1["conclusion"] == "SUCCESS"
        is_check_2_success = check_2["conclusion"] == "SUCCESS"
        assert is_check_1_success != is_check_2_success, (check_1, check_2)
        if not is_check_1_success:
            gh.assert_matching_comment(
                "TODO: add comment about lock failure here", since
            )
    finally:
        gh.close_pr(tacos_demo_pr1.url)
        gh.close_pr(tacos_demo_pr2.url)
