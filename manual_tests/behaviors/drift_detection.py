#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.functions import now
from lib.sh import sh
from manual_tests.lib import tacos_demo
from manual_tests.lib import tf
from manual_tests.lib.gh import workflow
from manual_tests.lib.gh.pr import PR
from manual_tests.lib.slice import Slices


@pytest.mark.xfail(reason="drift detection not yet implemented")
def test() -> None:
    tacos_demo.clone()
    slices = Slices.random()

    since = now()
    for slice in slices:
        slice.edit()

    try:
        # Pretend an hour has passed
        workflow.run("terraform_detect_drift.yml")

        # The drift detection workflow should have opened a PR to contain the drift
        pr = PR.wait_for("tacos/drift", since)

        # TODO: check that the plan matches what we expect
        assert pr.check("terraform_plan").wait(since).success
    finally:
        # Cleanup: roll back the infrastructure changes
        sh.run(("git", "reset", "--hard", "origin/main"))
        tf.apply()
