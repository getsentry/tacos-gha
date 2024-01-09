#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.sh import sh
from manual_tests.lib import tacos_demo
from manual_tests.lib.gh import gh
from manual_tests.lib.slice import Slices
from manual_tests.lib.xfail import XFailed


@pytest.mark.xfail(raises=XFailed)
def test(
    slices: Slices, test_name: str, demo: gh.LocalRepo, tacos_branch: gh.Branch
) -> None:
    sh.banner(
        f"Winner and Loser race to open a PR for the same slices: {slices}"
    )
    with (
        tacos_demo.PR.opened_for_slices(
            slices, test_name, demo, tacos_branch, branch=1
        ) as pr1,
        tacos_demo.PR.opened_for_slices(
            slices, test_name, demo, tacos_branch, branch=2
        ) as pr2,
    ):
        winner = loser = None
        for pr in (pr1, pr2):
            conclusion = pr.check("tacos_lock").wait().conclusion
            if conclusion == "SUCCESS":
                winner = pr
                sh.banner("Winner acquires the lock")
                print(winner)
            elif conclusion == "FAILURE":
                loser = pr
                sh.banner("Loser does not acquire the lock")
                print(winner)
            else:
                raise AssertionError(f"Unexpected conclusion: {conclusion}")

        assert winner is not None, winner
        assert winner.check("tacos_lock").wait().success

        sh.banner("Loser recieves a comment about the locking failure")
        try:
            assert loser is not None
        except AssertionError:
            raise XFailed("locking not yet implemented")
        assert (
            "lock failed, on slice prod/slice-3-vm, due to user1, PR #334 "
            in loser.comments(loser.since)
        )

        sh.banner("Winner closes their PR")
        winner.close()

        sh.banner("Loser adds the :taco::acquire-lock label")
        since = loser.add_label(":taco::acquire-lock")

        sh.banner("Loser acquires the lock")
        assert loser.check("tacos_lock").wait(since).success
