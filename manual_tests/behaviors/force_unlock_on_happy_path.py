#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.functions import now
from manual_tests.lib import gha
from manual_tests.lib import tacos_demo

TEST_NAME = __name__


@pytest.mark.xfail(reason="Comment not implemented yet.")
def test(pr: tacos_demo.PR) -> None:
    gha.assert_eventual_success(pr, "terraform_lock")

    since = now()
    pr.add_label(":taco::unlock")
    gha.assert_eventual_success(pr, "terraform_unlock", since)

    assert "INFO: Main branch clean, unlock successful." in pr.comments(
        since=since
    )
