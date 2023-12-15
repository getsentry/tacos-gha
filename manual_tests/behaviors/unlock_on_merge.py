#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.functions import now
from manual_tests.lib import tacos_demo
from manual_tests.lib.xfail import XFailed

TEST_NAME = __name__


@pytest.mark.xfail(raises=XFailed)
def test(pr: tacos_demo.PR) -> None:
    assert pr.check("terraform_lock").wait().success

    pr.approve()
    assert pr.approved()

    since = now()
    pr.merge()
    # fixme: raise XFailed(reason="Need other user's approval")

    assert pr.check("terraform_unlock").wait(since, timeout=6).success
