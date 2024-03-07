#!/usr/bin/env py.test
from __future__ import annotations

from lib.sh import sh
from spec.lib import tacos_demo

TEST_NAME = __name__


def test(pr: tacos_demo.PR) -> None:
    sh.banner("Wait for the terraform_plan check to complete")
    assert pr.check("Terraform Plan").wait().success

    sh.banner("A different user closes the PR")
    since = pr.close(tacos_demo.get_reviewer())

    sh.banner("Make sure the PR is unlocked.")
    assert pr.check("Terraform Unlock", "TACOS Unlock").wait(since).success
