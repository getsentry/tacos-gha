#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib import wait
from lib.functions import now
from manual_tests.lib import tacos_demo
from manual_tests.lib.xfail import XFailed

TEST_NAME = __name__


@pytest.mark.xfail(reason="Need other user's approval", raises=XFailed)
def test(pr: tacos_demo.PR) -> None:
    assert pr.check("terraform_lock").wait().success

    pr.approve()
    assert pr.approved()

    since = now()
    pr.merge()

    try:
        assert pr.check("terraform_unlock").wait(since, timeout=6).success
    except wait.TimeoutExpired:
        raise XFailed
