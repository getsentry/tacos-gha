#!/usr/bin/env py.test
from __future__ import annotations

from lib.functions import now
from manual_tests.lib import gh
from manual_tests.lib import gha
from manual_tests.lib import slice
from manual_tests.lib import tacos_demo

TEST_NAME = __name__


def test() -> None:
    slices = slice.random()

    tacos_demo.clone()
    since = now()
    tacos_demo_pr = tacos_demo.new_pr(TEST_NAME, slices)
    try:
        gha.assert_eventual_success("terraform_lock", since)
        gh.approve_pr(tacos_demo_pr.url)
        gh.assert_pr_is_approved(tacos_demo_pr.url)
        gh.add_label(tacos_demo_pr.url, ":taco::apply")
        gha.assert_eventual_success("terraform_apply", since)
        gh.merge_pr(tacos_demo_pr.url)
    except:
        gh.close_pr(tacos_demo_pr.branch)
    gha.assert_eventual_success("terraform_unlock", since)
