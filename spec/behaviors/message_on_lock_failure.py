#!/usr/bin/env py.test
from __future__ import annotations

from lib.sh import sh
from spec.lib import tacos_demo
from spec.lib.gh import gh
from spec.lib.slice import Slice
from spec.lib.slice import Slices

# TODO: improve the conflict message: "lock failed, on slice prod/slice-3-vm, due to user1, PR #334 "
CONFLICT_MESSAGE = """
$ sudo-gcp tf-lock-acquire
You are authenticated for the next hour as: tacos-gha-tf-state-admin@sac-dev-sa.iam.gserviceaccount.com
tf-lock-acquire: failure: not """


def assert_there_can_be_only_one(slice: Slice, *prs: tacos_demo.PR) -> None:
    sh.banner(f"Slice: {slice}")

    winner = loser = 0
    for pr in prs:
        comments = pr.get_comments_for_job("plan")
        check = pr.check(
            "Terraform Plan", f"tacos_plan ({pr.slices.subpath / slice})"
        ).ran()
        assert check is not None
        if check.conclusion == "SUCCESS":
            winner += 1
            print("Winner:", pr)
            assert CONFLICT_MESSAGE not in comments[slice]
        elif check.conclusion == "FAILURE":
            loser += 1
            print("Loser:", pr)
            assert CONFLICT_MESSAGE in comments[slice]
        else:
            raise AssertionError(check)

    # for some particular slice, there's one winner and one loser
    assert winner == loser == 1


def test(
    test_name: str, slices: Slices, demo: gh.LocalRepo, tacos_branch: gh.Branch
) -> None:
    with (
        tacos_demo.PR.opened_for_slices(
            slices, test_name, demo, tacos_branch, branch=1
        ) as pr1,
        tacos_demo.PR.opened_for_slices(
            slices, test_name, demo, tacos_branch, branch=2
        ) as pr2,
    ):
        for slice in slices:
            assert_there_can_be_only_one(slice, pr1, pr2)
