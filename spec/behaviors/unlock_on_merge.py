#!/usr/bin/env py.test
from __future__ import annotations

from spec.lib import tacos_demo

TEST_NAME = __name__


def test(pr: tacos_demo.PR) -> None:
    assert pr.check("Terraform Plan").wait().success

    since = pr.approve()
    assert pr.is_approved()

    pr.merge()

    assert pr.check("Terraform Unlock", "tacos_unlock").wait(since).success
