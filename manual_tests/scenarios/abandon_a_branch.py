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

    sh.banner(f"User 2 opens a PR for slices: {slices}")
    with tacos_demo.PR.opened_for_test(TEST_NAME, slices) as pr:
        sh.banner("User 1 acquires the lock")
        assert pr.check("terraform_lock").wait(since).success
        since = now()

        sh.banner("PR is aproved and applied")
        pr.approve()
        assert pr.approved()
        pr.add_label(":taco::apply")
        assert pr.check("terraform_apply").wait(since).success
        since = now()

        sh.banner("For various reasons, the PR is not merged. Time passes")
        # TODO: there should be a better way of simulating the PR being marked as stale.
        pr.add_label(":taco::stale")

        sh.banner("An attempt is made to notify the PR owner")
        assert pr.check("notify_owner").wait(since).success
        since = now()

        sh.banner("More time passes")
        # TODO: there should be a better way of simulating the PR being marked as abandoned.
        pr.add_label(":taco::abandoned")

        sh.banner("An attempt is made to notify other users of the repo")
        assert pr.check("notify_collaborators").wait(since).success
