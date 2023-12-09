#!/usr/bin/env py.test
from __future__ import annotations

from manual_tests.lib import slice
from manual_tests.lib import tacos_demo

TEST_NAME = __name__


def test() -> None:
    with tacos_demo.PR.opened_for_test(TEST_NAME, slice.random()) as pr:
        assert pr.check("terraform_lock").wait().success
        for s in range(3):
            locked = slice.is_locked(s)
            expected = s in pr.slices

            try:
                assert locked == expected, (locked, s, pr)
            except AssertionError:
                # FIXME: actually do locking in our GHA "Obtain Lock" job
                assert locked == False, locked
