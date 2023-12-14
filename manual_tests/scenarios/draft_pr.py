#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.functions import now
from lib.sh import sh
from manual_tests.lib import tacos_demo
from manual_tests.lib.slice import Slices

TEST_NAME = __name__


@pytest.mark.xfail(reason="Draft PRs still try to lock")
def test() -> None:
    slices = Slices.random()
    with tacos_demo.PR.opened_for_test(
        TEST_NAME, slices, draft=True
    ) as pr:
        sh.banner("Draft PR opened:", pr.url)

        # The terraform_plan check should run automatically when the PR is opened
        sh.banner("Wait for the terraform_plan check to complete")
        pr.check("terraform_plan").wait(pr.since).success

        # The terraform_lock check should not run automatically when the PR is a draft
        sh.banner("Make sure the terraform_lock check did not run")
        pr.check("terraform_lock").assert_not_ran(pr.since)

        # Since the lock was not aquired, applying the plan should fail
        sh.banner("Apply the plan")
        pr.add_label(":taco::apply")

        # The terraform_apply check should fail
        assert not pr.check("terraform_apply").wait(pr.since).success

        # Another user should be able to aquire the lock(s)
        sh.banner("Open a second PR for the same slices")
        with tacos_demo.PR.opened_for_test(
            TEST_NAME, slices, draft=False # This one is not a draft
        ) as pr2:
            sh.banner("Non-draft PR opened:", pr2.url)

            # The terraform_plan check should run automatically when the PR is opened
            sh.banner("Wait for the terraform_plan check to complete")
            pr2.check("terraform_plan").wait(pr2.since).success

            # This PR should aquire the lock
            sh.banner("Make sure the terraform_lock check ran successfully")
            pr2.check("terraform_lock").wait(pr2.since).success
