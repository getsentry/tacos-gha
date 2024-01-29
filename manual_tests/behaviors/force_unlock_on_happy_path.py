#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from manual_tests.lib import tacos_demo
from manual_tests.lib.xfail import XFailed

TEST_NAME = __name__


@pytest.mark.xfail(raises=XFailed)
def test(pr: tacos_demo.PR) -> None:
    assert pr.check("Terraform Plan").wait().success
    slices = pr.get_plans().keys()
    for slice in slices:
        assert slice.is_locked(), f"Slice {slice} is not locked"

    since = pr.add_label(":taco::unlock")
    assert pr.check("Terraform Unlock").wait(since).success
    for slice in slices:
        assert not slice.is_locked(), f"Slice {slice} is still locked"

    
    expected_msg = "Terraform lock state:\n\n"
    for slice in slices:
        expected_msg += (
            f"Slice {slice}\n"
            "Terraform state has been successfully unlocked!\n"
            "\n"
            "The state has been unlocked, and Terraform commands should now be able to\n"
            "obtain a new lock on the remote state.\n"
            "\n"
            "\n"
        )
    expected_msg += "\n\n\n"

    try:
        assert expected_msg in pr.comments(
            since=since
        )
    except AssertionError:
        raise XFailed("still need to post message from unlock")
