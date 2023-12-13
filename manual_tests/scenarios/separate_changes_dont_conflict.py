#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.functions import now
from lib.sh import sh
from manual_tests.lib import tacos_demo
from manual_tests.lib.slice import Slice
from manual_tests.lib.slice import Slices

TEST_NAME = __name__


@pytest.mark.xfail(reason="Locking not yet implemented")
def test() -> None:
    slice1 = Slices([Slice(0)])
    slice2 = Slices([Slice(1)])

    since = now()
    tacos_demo.clone()
    sh.banner(f"User 1 opens a PR for slice: {slice1}")
    sh.banner(f"User 2 opens a PR for slice: {slice2}")
    with (
        tacos_demo.PR.opened_for_test(TEST_NAME, slice1) as pr1,
        tacos_demo.PR.opened_for_test(TEST_NAME, slice2) as pr2,
    ):
        sh.banner("User 1 acquires the lock")
        assert pr1.check("terraform_lock").wait(since).success

        sh.banner("User 2 acquires the lock")
        assert pr2.check("terraform_lock").wait(since).success
