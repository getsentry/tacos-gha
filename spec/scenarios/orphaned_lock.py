#!/usr/bin/env py.test
from __future__ import annotations

from pytest import fixture

from lib.sh import sh
from spec.lib import tacos_demo
from spec.lib.gh import gh
from spec.lib.slice import Slices


@fixture
def slices(slices: Slices) -> Slices:
    # get one random slice, but make sure its used for both PRs
    return slices.random(count=1)


def test_closed(
    slices: Slices, test_name: str, demo: gh.LocalRepo, tacos_branch: gh.Branch
) -> None:
    sh.banner(
        f"Orphan slice by reverting and closing PR: {slices} and open a PR for the same slice that unlocks it"
    )
    with (
        tacos_demo.PR.opened_for_slices(
            slices, test_name, demo, tacos_branch, branch=1
        ) as pr1,
    ):
        # check that pr1 plans correctly and holds lock for slice
        slices.edit()
        pr1.check("Terraform Plan").wait().success
        slices.assert_locked()

        # revert slice
        slices.revert()

        # orphan slices from pr1
        pr1.close()

        slices.assert_locked()

    with (
        tacos_demo.PR.opened_for_slices(
            slices, test_name, demo, tacos_branch, branch=2
        ) as pr2,
    ):
        # check that pr2 plans correctly
        assert pr2.check("Terraform Plan").wait().success


def test_drafted(
    slices: Slices, test_name: str, demo: gh.LocalRepo, tacos_branch: gh.Branch
) -> None:
    sh.banner(
        f"Orphan slice by reverting and moving PR to draft: {slices} and open a PR for the same slice that unlocks it"
    )
    with (
        tacos_demo.PR.opened_for_slices(
            slices, test_name, demo, tacos_branch, branch=1
        ) as pr1,
    ):
        # check that pr1 plans correctly and holds lock for slice
        slices.edit()
        pr1.check("Terraform Plan").wait().success
        slices.assert_locked()

        # revert slice
        slices.revert()

        # orphan slices from pr1
        pr1.toggle_draft()

        slices.assert_locked()

        with (
            tacos_demo.PR.opened_for_slices(
                slices, test_name, demo, tacos_branch, branch=2
            ) as pr2,
        ):
            # check that pr2 plans correctly
            assert pr2.check("Terraform Plan").wait().success
