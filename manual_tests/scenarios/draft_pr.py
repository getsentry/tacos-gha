#!/usr/bin/env py.test
from __future__ import annotations

from lib.sh import sh
from manual_tests.lib import tacos_demo
from manual_tests.lib.gh import gh
from manual_tests.lib.slice import Slices


def test(
    slices: Slices, test_name: str, demo: gh.LocalRepo, tacos_branch: gh.Branch
) -> None:
    with tacos_demo.PR.opened_for_slices(
        slices, test_name, demo, tacos_branch, draft=True
    ) as pr:
        sh.banner("Draft PR opened:", pr.url)

        # The terraform_plan check should run automatically when the PR is opened
        sh.banner("Wait for the terraform_plan check to complete")
        assert pr.check("Terraform Plan").wait(pr.since).success

        # The slices should not be locked
        sh.banner("Make sure the slices are not locked")
        for slice in slices:
            assert not slice.is_locked()

        # Since this PR is a draft, it should not be able to apply the plan
        sh.banner("Try to apply the plan for a draft PR")
        since = pr.add_label(":taco::apply")

        # The terraform_apply check should not run automatically when the PR is a draft
        assert pr.check("Terraform Apply", "tacos_apply").wait(since).skipped

        # Another user should be able to aquire the lock(s)
        sh.banner("Open a second, non-draft PR for the same slices")
        with tacos_demo.PR.opened_for_slices(
            slices,
            f"{test_name}-2",
            demo,
            tacos_branch,
            draft=False,  # This one is not a draft
        ) as pr2:
            # The terraform_plan check should run automatically when the PR is opened
            sh.banner(
                "Wait for the terraform_plan check to complete successfully"
            )
            pr2.check("Terraform Plan").wait().success

            # This PR should aquire the lock
            sh.banner("Make sure the terraform_lock checks ran successfully")
            pr2.slices.assert_locked()

            # Since this is not a draft PR, it should be able to apply the plan
            sh.banner("Apply the plan for the second PR")
            since = pr2.add_label(":taco::apply")
            pr2.check("Terraform Apply").wait(since).success

            since = pr2.approve()
            assert pr2.is_approved()

            # Merge the second PR
            sh.banner("Merge the second PR")
            pr2.merge()
