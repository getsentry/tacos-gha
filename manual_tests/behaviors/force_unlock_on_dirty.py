#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.functions import now
from manual_tests.lib import gha
from manual_tests.lib import tacos_demo

TEST_NAME = __name__


@pytest.mark.xfail(reason="still need to post comment during action")
def test(pr: tacos_demo.PR) -> None:
    gha.assert_eventual_success(pr, "terraform_lock")

    since = now()
    pr.add_label(":taco::apply")
    gha.assert_eventual_success(pr, "terraform_apply", since)

    since = now()
    pr.add_label(":taco::unlock")
    gha.assert_eventual_success(pr, "terraform_unlock", since)
    assert "WARNING: Unlocked while applied but not merged!" in pr.comments(
        since=since
    )
    # TODO: maybe check for the opening of the drift remediation branch.
