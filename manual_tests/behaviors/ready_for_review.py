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

        sh.banner("Convert Draft PR to non-draft")
        since = pr.toggle_draft()

        # The terraform_plan check should run automatically when the PR is marked ready
        sh.banner("Wait for the terraform_plan check to complete")
        assert pr.check("Terraform Plan").wait(since).success

        # This PR should aquire the lock
        sh.banner("Make sure the terraform_lock checks ran successfully")
        pr.slices.assert_locked()
