#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from manual_tests.lib import tacos_demo
from manual_tests.lib.xfail import XFailed


@pytest.mark.xfail(raises=XFailed)
def test(pr: tacos_demo.PR) -> None:
    assert pr.check("terraform_lock").wait().success
    pr.slices.assert_locked()
