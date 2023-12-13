#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.functions import now
from manual_tests.lib import slice
from manual_tests.lib import tacos_demo

TEST_NAME = __name__


@pytest.mark.xfail(reason="Locking not yet implemented")
def test() -> None:
    slices = slice.random()

    since = now()
    tacos_demo.clone()
    pr1 = tacos_demo.PR.for_test(TEST_NAME, slices)
    pr1_open = True
    pr2 = tacos_demo.PR.for_test(TEST_NAME, slices)
    try:
        assert pr1.check("terraform_lock").wait(since).success
        assert "TODO: add comment about lock failure here" in pr2.comments(
            since=since
        )
        pr1.close()
        pr1_open = False
        pr2.add_label(":taco::acquire-lock")
        since = now()
        assert pr2.check("terraform_lock").wait(since).success
    finally:
        if pr1_open:
            pr1.close()
        pr2.close()
