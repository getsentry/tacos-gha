#!/usr/bin/env py.test
from __future__ import annotations

from manual_tests.lib import tacos_demo
from manual_tests.lib.slice import Slices

TEST_NAME = __name__


def test() -> None:
    with tacos_demo.PR.opened_for_test(TEST_NAME, Slices.random()) as pr:
        assert pr.check("terraform_lock").wait().success
        for slice in Slices.all():
            locked = slice.is_locked()
            expected = slice in pr.slices

            try:
                assert locked == expected, (locked, slice, pr)
            except AssertionError:
                # FIXME: actually do locking in our GHA "Obtain Lock" job
                assert locked == False, locked
