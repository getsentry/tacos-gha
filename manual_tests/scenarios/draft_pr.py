#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.sh import sh
from manual_tests.lib import tacos_demo
from manual_tests.lib.slice import Slices
from manual_tests.lib.xfail import XFailed

TEST_NAME = __name__


@pytest.mark.xfail(raises=XFailed)
def test(slices: Slices) -> None:
    with tacos_demo.PR.opened_for_slices(slices, TEST_NAME, draft=True) as pr:
        sh.banner("Draft PR opened:", pr.url)

        # The terraform_plan check should run automatically when the PR is opened
        sh.banner("Wait for the terraform_plan check to complete")
        assert pr.check("terraform_plan").wait(pr.since).success

        # The terraform_lock check should not run automatically when the PR is a draft
        sh.banner("Make sure the terraform_lock check did not run")
        assert pr.check("terraform_lock").wait(pr.since).skipped

        # Since this PR is a draft, it should not be able to apply the plan
        sh.banner("Try to apply the plan for a draft PR")
        since = pr.add_label(":taco::apply")

        # The terraform_apply check should not run automatically when the PR is a draft
        assert pr.check("terraform_apply").wait(pr.since).skipped

        # Another user should be able to aquire the lock(s)
        sh.banner("Open a second, non-draft PR for the same slices")
        with tacos_demo.PR.opened_for_slices(
            slices, f"{TEST_NAME}-2", draft=False  # This one is not a draft
        ) as pr2:
            # The terraform_plan check should run automatically when the PR is opened
            sh.banner(
                "Wait for the terraform_plan check to complete successfully"
            )
            pr2.check("terraform_plan").wait().success

            # This PR should aquire the lock
            sh.banner("Make sure the terraform_lock checks ran successfully")
            for slice in slices:
                assert pr2.check(f"terraform_lock ({slice})").wait().success

            # Since this is not a draft PR, it should be able to apply the plan
            sh.banner("Apply the plan for the second PR")
            since = pr2.add_label(":taco::apply")
            pr2.check("terraform_apply").wait(since).success

            # Merge the second PR
            sh.banner("Merge the second PR")
            pr2.merge()
