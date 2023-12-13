#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.functions import now
from lib.sh import sh
from manual_tests.lib import slice
from manual_tests.lib import tacos_demo
from manual_tests.lib import tf
from manual_tests.lib.gh.pr import PR
from manual_tests.lib.gh.workflow import trigger_workflow


@pytest.mark.xfail(reason="drift detection not yet implemented")
def test() -> None:
    tacos_demo.clone()
    slices = slice.random()

    since = now()
    for s in slices:
        slice.edit(s)

    # Make infrastructure changes out-of-band
    tf.apply()

    try:
        # Pretend an hour has passed
        trigger_workflow("terraform_detect_drift.yml")

        # The drift detection workflow should have opened a PR to contain the drift
        pr = PR.wait_for_pr("tacos/drift", since)

        # TODO: check that the plan matches what we expect
        assert pr.check("terraform_plan").wait(since).success
    finally:
        # Cleanup: roll back the infrastructure changes
        sh.run(("git", "reset", "--hard", "origin/main"))
        tf.apply()
