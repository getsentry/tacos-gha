#!/usr/bin/env py.test
from __future__ import annotations

from datetime import datetime

import pytest

from lib.functions import now
from lib.functions import one
from lib.sh import sh
from lib.tacos import conflict_detection
from spec.lib import tacos_demo
from spec.lib.gh import gh
from spec.lib.slice import Slices


def assert_conflict_notification(pr: tacos_demo.PR, since: datetime) -> None:
    assert pr.check("Terraform Conflict Detection").wait(since).success
    assert ":taco::conflict" in pr.labels()
    comment = one(pr.get_comments_for_job(conflict_detection.JOB).values())
    assert comment == conflict_detection.MERGE_CONFLICT_MESSAGE


def assert_no_conflict_notification(
    pr: tacos_demo.PR, since: datetime
) -> None:
    assert pr.check("Terraform Conflict Detection").wait(since).completed
    assert ":taco::conflict" not in pr.labels()
    assert not pr.get_comments_for_job(conflict_detection.JOB)


def test(
    test_name: str, slices: Slices, demo: gh.LocalRepo, tacos_branch: gh.Branch
) -> None:
    sh.banner("two PRs race, but only one can merge first...")
    with (
        tacos_demo.PR.opened_for_slices(
            slices, test_name, demo, tacos_branch, branch=1
        ) as winner,
        tacos_demo.PR.opened_for_slices(
            slices, test_name, demo, tacos_branch, branch=2
        ) as loser,
    ):
        sh.banner("approve and merge both PR")
        since = winner.approve()
        winner.merge()
        loser.approve()

        with pytest.raises(sh.CalledProcessError):
            loser.merge()  # not mergeable

        sh.banner("check for conflict warning")
        assert_conflict_notification(loser, since)
        sh.banner("check for no conflict warning on winner")
        assert_no_conflict_notification(winner, since)

        sh.banner("resolve the conflict and check again")
        since = now()
        sh.run(("git", "checkout", loser.branch))
        sh.run(("git", "pull", "--rebase=false", "--strategy=ours"))
        sh.run(
            # shouldn't need force, since we merged
            ("git", "push", "origin", "HEAD")
        )
        assert_no_conflict_notification(loser, since)
