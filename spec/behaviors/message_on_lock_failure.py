#!/usr/bin/env py.test
from __future__ import annotations

from spec.lib import tacos_demo
from spec.lib.gh import gh
from spec.lib.slice import Slices
from spec.lib.testing import assert_there_can_be_only_one


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
