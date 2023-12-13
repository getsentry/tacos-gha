#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.functions import now
from lib.sh import sh
from manual_tests.lib import tacos_demo
from manual_tests.lib.slice import Slices

TEST_NAME = __name__


@pytest.mark.xfail(reason="Locking not yet implemented")
def test() -> None:
    slices = Slices.random()

    since = now()
    tacos_demo.clone()

    sh.banner(f"User 1 opens a PR for slices: {slices}")
    pr1 = tacos_demo.PR.for_test(TEST_NAME, slices)

    pr2 = None
    try:
        sh.banner("User 1 acquires the lock")
        assert pr1.check("terraform_lock").wait(since).success

        sh.banner("User 2 opens a PR for the same slices")
        pr2 = tacos_demo.PR.for_test(TEST_NAME, slices)

        sh.banner("User 2 recieves a comment about the locking failure")
        assert "TODO: add comment about lock failure here" in pr2.comments(
            since=since
        )

        sh.banner("User 1 closes their PR")
        pr1.close()

        sh.banner("User 2 adds the :taco::acquire-lock label")
        pr2.add_label(":taco::acquire-lock")
        since = now()

        sh.banner("User 2 acquires the lock")
        assert pr2.check("terraform_lock").wait(since).success
    finally:
        pr1.close()
        if pr2 is not None:
            pr2.close()
