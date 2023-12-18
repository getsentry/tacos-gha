#!/usr/bin/env py.test
from __future__ import annotations

from pathlib import Path

import pytest

from lib.functions import now
from lib.sh import sh
from manual_tests.lib import tacos_demo
from manual_tests.lib.slice import Slices


@pytest.mark.xfail(reason="Locking not yet implemented")
def test(workdir: Path, test_name: str) -> None:
    all_slices = Slices.from_path(workdir)
    slices1 = all_slices.random()
    slices2 = all_slices - slices1

    since = now()
    sh.banner(f"User 1 opens a PR for some slices: {slices1}")
    sh.banner(f"User 2 opens a PR for separate slices: {slices2}")
    with (
        tacos_demo.PR.opened_for_slices(slices1, test_name) as pr1,
        tacos_demo.PR.opened_for_slices(slices2, test_name) as pr2,
    ):
        sh.banner("User 1 acquires the lock")
        assert pr1.check("terraform_lock").wait(since).success

        sh.banner("User 2 acquires the lock")
        assert pr2.check("terraform_lock").wait(since).success
