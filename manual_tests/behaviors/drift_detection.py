#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.functions import now
from lib.sh import sh
from manual_tests.lib import slice
from manual_tests.lib import tacos_demo
from manual_tests.lib import tf
from manual_tests.lib.gh.pr import wait_for_pr
from manual_tests.lib.gh.workflow import trigger_workflow


@pytest.mark.xfail(reason="drift detection not yet implemented")
def test() -> None:
    tacos_demo.clone()
    slices = slice.random()

    since = now()
    for s in slices:
        slice.edit(s, False)
    tf.apply()
    trigger_workflow("drift-detection")
    pr = wait_for_pr("tacos/drift", since)
    assert pr.check("terraform_plan").wait(since).success
    # TODO: check that the plan matches what we expect
    # Cleanup option 1: roll forward (merge PR)
    # Cleanup option 2: roll back (apply main branch and close PR) (easier)
    sh.run(("git", "checkout", "main"))
    tf.apply()
