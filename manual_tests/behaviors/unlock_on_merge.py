#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.functions import now
from manual_tests.lib import slice
from manual_tests.lib import tacos_demo

TEST_NAME = __name__


@pytest.mark.xfail(reason="Need other user's approval")
def test() -> None:
    slices = slice.random()

    since = now()
    tacos_demo.clone()
    pr = tacos_demo.PR.for_test(TEST_NAME, slices)
    try:
        assert pr.check("terraform_lock").wait(since).success
        since = now()
        pr.approve()
        assert pr.approved()
        pr.add_label(":taco::apply")
        assert pr.check("terraform_apply").wait(since).success
        since = now()
        pr.merge_pr()
    except Exception:  # If we manage to merge, we don't need to close.
        pr.close()
        raise
    assert pr.check("terraform_unlock").wait(since, timeout=6).success
