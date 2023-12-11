#!/usr/bin/env py.test
from __future__ import annotations

from lib.functions import now
from lib.sh import sh
from manual_tests.lib import gh
from manual_tests.lib import slice
from manual_tests.lib import tacos_demo
from manual_tests.lib import tf


def test() -> None:
    slices = slice.random()

    since = now()
    tacos_demo.clone()
    for s in slices:
        slice.edit(s, False)
    tf.apply()
    gh.workflow.trigger_workflow("drift-detection")
    pr = gh.pr.wait_for_pr("tacos/drift", since)
    assert pr.check("terraform_plan").wait(since).success
    # TODO: check that the plan matches what we expect
    # Cleanup option 1: roll forward (merge PR)
    # Cleanup option 2: roll back (apply main branch and close PR) (easier)
    sh.run(("git", "checkout", "main"))
    tf.apply()
