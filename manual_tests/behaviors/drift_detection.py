#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib import wait
from lib.functions import now
from lib.sh import sh
from manual_tests.lib import tf
from manual_tests.lib.gh import workflow
from manual_tests.lib.gh.pr import PR
from manual_tests.lib.slice import Slices
from manual_tests.lib.xfail import XFailed


@pytest.mark.xfail(raises=XFailed)
def test(slices: Slices) -> None:
    sh.banner("Make infrastructure changes out-of-band")
    since = now()
    slices.edit()
    tf.apply(slices.workdir)

    try:
        sh.banner("Pretend an hour has passed")
        workflow.run("terraform_detect_drift.yml")

        sh.banner("wait for the drift detection workflow to open a PR")
        try:
            pr = PR.wait_for("tacos/drift", since, timeout=6)
        except wait.TimeoutExpired:
            raise XFailed("tacos/drift branch not created")

        sh.banner("TODO: check that the plan matches what we expect")
        assert pr.check("terraform_plan").wait(since).success
    finally:
        sh.banner("Cleanup: roll back the infrastructure changes")
        sh.run(("git", "-C", slices.workdir, "reset", "--hard", "origin/main"))
        tf.apply(slices.workdir)
