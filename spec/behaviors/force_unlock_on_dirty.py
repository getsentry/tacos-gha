#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from spec.lib import tacos_demo
from spec.lib.xfail import XFailed

TEST_NAME = __name__


@pytest.mark.xfail(raises=XFailed)
def test(pr: tacos_demo.PR) -> None:
    assert pr.check("Terraform Lock").wait().success

    since = pr.add_label(":taco::apply")
    assert pr.check("Terraform Apply").wait(since).success

    since = pr.add_label(":taco::unlock")
    assert pr.check("Terraform Unlock").wait(since).success
    try:
        assert (
            "WARNING: Unlocked while applied but not merged!"
            in pr.comments(since=since)
        )
    except AssertionError:
        raise XFailed("Comment not implemented yet.")

    # TODO: maybe check for the opening of the drift remediation branch.
