#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from manual_tests.lib import tacos_demo
from manual_tests.lib.xfail import XFailed

TEST_NAME = __name__


@pytest.mark.xfail(raises=XFailed)
def test(pr: tacos_demo.PR) -> None:
    # TODO: use slice name
    assert pr.check("Terraform Lock").wait().success

    since = pr.approve()
    assert pr.approved()

    pr.merge()

    assert pr.check("Terraform Unlock").wait(since, timeout=6).success
