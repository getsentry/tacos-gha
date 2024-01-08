#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.sh import sh
from manual_tests.lib import tacos_demo
from manual_tests.lib.xfail import XFailed


@pytest.mark.xfail(raises=XFailed)
def test(pr: tacos_demo.PR) -> None:
    sh.banner("PR is approved and applied")
    pr.approve()
    assert pr.approved()

    since = pr.add_label(":taco::apply")
    assert pr.check("Terraform Apply", "tacos-gha / main").wait(since).success

    sh.banner("For various reasons, the PR is not merged. Time passes")
    # TODO: there should be a better way of simulating the PR being marked as stale.
    since = pr.add_label(":taco::stale")

    sh.banner("An attempt is made to notify the PR owner")
    try:
        assert pr.check("Notify Owner", "notify_owner").wait(since).success
    except AssertionError:
        raise XFailed("notify_owner action does not exist")

    sh.banner("More time passes")
    # TODO: there should be a better way of simulating the PR being marked as abandoned.
    since = pr.add_label(":taco::abandoned")

    sh.banner("An attempt is made to notify other users of the repo")
    assert pr.check("Notify Collaborators", "notify_collaborators").wait(since).success
