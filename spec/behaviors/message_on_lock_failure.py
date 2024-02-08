#!/usr/bin/env py.test
from __future__ import annotations

from spec.lib import tacos_demo
from spec.lib.gh import gh
from spec.lib.slice import Slices

# TODO: improve the conflict message: "lock failed, on slice prod/slice-3-vm, due to user1, PR #334 "
CONFLICT_MESSAGE = """
$ sudo-gcp tf-lock-acquire
You are authenticated for the next hour as: tacos-gha-tf-state-admin@sac-dev-sa.iam.gserviceaccount.com
tf-lock-acquire: failure: not """


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
        checks: dict[tacos_demo.PR, gh.CheckRun] = {
            pr1: pr1.check("Terraform Plan").wait(),
            pr2: pr2.check("Terraform Plan").wait(),
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

        assert {check.conclusion for check in checks.values()} == {
            "SUCCESS",
            "FAILURE",
        }
