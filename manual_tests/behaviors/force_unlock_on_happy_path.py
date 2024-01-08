#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from manual_tests.lib import tacos_demo
from manual_tests.lib.xfail import XFailed

TEST_NAME = __name__


@pytest.mark.xfail(raises=XFailed)
def test(pr: tacos_demo.PR) -> None:
    # TODO: use slice name
    assert pr.check("Terraform Lock", "tacos-gha / main").wait().success

    since = pr.add_label(":taco::unlock")
    assert pr.check("Terraform Unlock", "terraform_unlock").wait(since).success

    try:
        assert "INFO: Main branch clean, unlock successful." in pr.comments(
            since=since
        )
    except AssertionError:
        raise XFailed("still need to post message from unlock")
