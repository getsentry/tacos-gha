#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.functions import now
from manual_tests.lib import tacos_demo

TEST_NAME = __name__


@pytest.mark.xfail(reason="Comment not implemented yet.")
def test(pr: tacos_demo.PR) -> None:
    assert pr.check("terraform_lock").wait().success

    since = now()
    pr.add_label(":taco::apply")
    assert pr.check("terraform_apply").wait(since).success

    since = now()
    pr.add_label(":taco::unlock")
    assert pr.check("terraform_unlock").wait(since).success
    assert "WARNING: Unlocked while applied but not merged!" in pr.comments(
        since=since
    )
    # TODO: maybe check for the opening of the drift remediation branch.
