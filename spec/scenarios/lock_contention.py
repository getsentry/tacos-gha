#!/usr/bin/env py.test
from __future__ import annotations

from lib.sh import sh
from spec.lib import tacos_demo
from spec.lib.gh import gh
from spec.lib.slice import Slices

MESSAGE = """
$ sudo-gcp tf-lock-acquire
You are authenticated for the next hour as: tacos-gha-tf-state-admin@sac-dev-sa.iam.gserviceaccount.com
tf-lock-acquire: failure: not """


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
            conclusion = pr.check("Terraform Plan").wait().conclusion
            if conclusion == "SUCCESS":
                winner = pr
                sh.banner("Winner acquires the lock")
                print(winner)
            elif conclusion == "FAILURE":
                loser = pr
                sh.banner("Loser does not acquire the lock")
                print(loser)
            else:
                raise AssertionError(f"Unexpected conclusion: {conclusion}")

        assert winner is not None, winner
        assert winner.check("Terraform Plan").wait().success

        sh.banner("Loser recieves a comment about the locking failure")
        assert loser is not None
        comments = loser.get_comments_for_job("plan")
        for slice in loser.slices:
            assert MESSAGE in comments[slice]

        sh.banner("Winner doesn't")
        comments = winner.get_comments_for_job("plan")
        for slice in winner.slices:
            assert MESSAGE not in comments[slice]

        sh.banner("Winner closes their PR")
        since = winner.close()
        assert winner.check("Terraform Unlock").wait().success

        # TODO: add a :taco::lock label
        sh.banner("Loser gets the lock, using :taco::lock label")
        since = loser.add_label(":taco::plan")
        assert loser.check("Terraform Plan").wait(since).success
