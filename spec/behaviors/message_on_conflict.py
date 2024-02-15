#!/usr/bin/env py.test
from __future__ import annotations

from lib.sh import sh
from spec.lib import tacos_demo
from spec.lib.gh import gh
from spec.lib.slice import Slices

CONFLICT_MESSAGE = """This PR currently has a merge conflict, which is preventing
other TACOS jobs from running. Please solve the conflict and
then try again."""


def test(
    test_name: str, slices: Slices, demo: gh.LocalRepo, tacos_branch: gh.Branch
) -> None:
    sh.banner("Open a first PR, and open a second draft PR")
    with (
        tacos_demo.PR.opened_for_slices(
            slices, test_name, demo, tacos_branch, branch=1
        ) as pr1,
        tacos_demo.PR.opened_for_slices(
            slices, test_name, demo, tacos_branch, branch=2, draft=True
        ) as pr2,
    ):
        sh.banner("Plan, approve and merge the first PR")
        assert pr1.check("Terraform Plan").wait().success
        since = pr1.approve()
        pr1.merge()
        assert (
            pr1.check("Terraform Unlock", "tacos_unlock").wait(since).success
        )
        sh.banner("Set the second PR as ready and check for the conflict")
        since = pr2.toggle_draft()
        assert pr2.check("Terraform Conflict").wait(since).success
        _, comment = pr2.get_comments_for_job("conflict").popitem()
        assert CONFLICT_MESSAGE in comment
