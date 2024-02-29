#!/usr/bin/env py.test
from __future__ import annotations

from lib.sh import sh
from spec.lib import tacos_demo
from spec.lib.gh import gh
from spec.lib.slice import Slice
from spec.lib.slice import Slices

CONFLICT_MESSAGE = """
$ sudo-gcp tf-lock-acquire
You are authenticated for the next hour as: tacos-gha-tf-state-admin@sac-dev-sa.iam.gserviceaccount.com

$ tf-lock-info .
tf-lock-acquire: Lock failed. User """


def assert_there_can_be_only_one(slice: Slice, *prs: tacos_demo.PR) -> None:
    sh.banner(f"Slice: {slice}")

    checks: dict[tacos_demo.PR, gh.CheckRun] = {
        pr: pr.check(
            "Terraform Plan", f"tacos_plan ({pr.slices.subpath / slice})"
        ).wait()
        for pr in prs
    }
    assert {check.conclusion for check in checks.values()} == {
        "SUCCESS",
        "FAILURE",
    }

    for pr, check in checks.items():
        comments = pr.get_comments_for_job("plan")
        if check.conclusion == "SUCCESS":
            print("Winner:", pr.url)
            for slice in pr.slices:
                assert CONFLICT_MESSAGE not in comments[slice]
        elif check.conclusion == "FAILURE":
            print("Loser:", pr.url)
            for slice in pr.slices:
                assert CONFLICT_MESSAGE in comments[slice]
        else:
            raise AssertionError(check)


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
