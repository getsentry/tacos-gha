#!/usr/bin/env py.test
from __future__ import annotations

from spec.lib import tacos_demo


def test(pr: tacos_demo.PR) -> None:
    assert pr.check("Terraform Plan").wait().success
    pr.slices.assert_locked()
