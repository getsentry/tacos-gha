#!/usr/bin/env py.test
from __future__ import annotations

from manual_tests.lib import tacos_demo


def test(pr: tacos_demo.PR) -> None:
    assert pr.check("terraform_lock").wait().success
    pr.slices.assert_locked()
