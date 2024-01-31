#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.sh import sh
from lib.types import OSPath
from spec.lib import tacos_demo
from spec.lib.gh import gh
from spec.lib.slice import Slices


@pytest.mark.xfail(reason="Locking not yet implemented")
def test(
    workdir: OSPath,
    test_name: str,
    demo: gh.LocalRepo,
    tacos_branch: gh.Branch,
) -> None:
    all_slices = Slices.from_path(workdir)
    slices1 = all_slices.random()
    slices2 = all_slices - slices1

    sh.banner(f"User 1 opens a PR for some slices: {slices1}")
    sh.banner(f"User 2 opens a PR for separate slices: {slices2}")
    with (
        tacos_demo.PR.opened_for_slices(
            slices1, test_name, demo, tacos_branch
        ) as pr1,
        tacos_demo.PR.opened_for_slices(
            slices2, test_name, demo, tacos_branch
        ) as pr2,
    ):
        sh.banner("User 1 acquires the lock")
        assert pr1.check("Terraform Lock").wait().success

        sh.banner("User 2 acquires the lock")
        assert pr2.check("Terraform Lock").wait().success
