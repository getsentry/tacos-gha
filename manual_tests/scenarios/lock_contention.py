#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.functions import now
from lib.sh import sh
from manual_tests.lib import tacos_demo
from manual_tests.lib.slice import Slices
from manual_tests.lib.xfail import XFailed


# reason="Locking not yet implemented"
@pytest.mark.xfail(raises=XFailed)
def test(slices: Slices, test_name: str) -> None:
    since = now()

    sh.banner(f"User 1 opens a PR for slices: {slices}")
    pr1 = tacos_demo.PR.for_slices(slices, test_name)

    pr2 = None
    try:
        sh.banner("User 1 acquires the lock")
        assert pr1.check("terraform_lock").wait(since).success

        sh.banner("User 2 opens a PR for the same slices")
        pr2 = tacos_demo.PR.for_slices(slices, test_name)

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
