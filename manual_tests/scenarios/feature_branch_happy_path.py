#!/usr/bin/env py.test
from __future__ import annotations

from manual_tests.lib import gha
from manual_tests.lib import slice
from manual_tests.lib import tacos_demo


def test(pr: tacos_demo.PR) -> None:
    gha.assert_eventual_success(pr, "terraform_lock")
    slice.assert_locked(pr.slices)
