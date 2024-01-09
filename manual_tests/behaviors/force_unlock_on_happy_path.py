#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from manual_tests.lib import tacos_demo
from manual_tests.lib.xfail import XFailed

TEST_NAME = __name__


@pytest.mark.xfail(raises=XFailed)
def test(pr: tacos_demo.PR) -> None:
    assert pr.check("tacos_lock").wait().success
    # pr.assert_locked()

    since = pr.add_label(":taco::unlock")
    assert pr.check("tacos_unlock").wait(since).success

    try:
        assert "INFO: Main branch clean, unlock successful." in pr.comments(
            since=since
        )
    except AssertionError:
        raise XFailed("still need to post message from unlock")
