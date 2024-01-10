#!/usr/bin/env py.test
from __future__ import annotations

from datetime import datetime

import pytest

from lib import wait
from lib.sh import sh
from manual_tests.lib import tacos_demo
from manual_tests.lib import tf
from manual_tests.lib.gh import workflow
from manual_tests.lib.slice import Slices
from manual_tests.lib.xfail import XFailed


def create_drift(slices: Slices) -> datetime:
    sh.banner("somebody changes infrastructure out of band")
    slices.edit()
    tf.apply(slices.workdir)

    sh.banner("pretend an hour passed: trigger the drift-scan job")
    return workflow.run("terraform_detect_drift.yml")


@pytest.mark.xfail(raises=XFailed)
def test_roll_forward(slices: Slices) -> None:
    since = create_drift(slices)

    sh.banner("check out automatically-created PR")
    try:
        pr = tacos_demo.PR.wait_for("tacos/drift", since, timeout=6)
    except wait.TimeoutExpired:
        raise XFailed("tacos/drift branch not created")

    sh.banner("commit out-of-band changes so plan is clean")
    # Cleanup: roll back the infrastructure changes
    branch = "tacos/drift"
    sh.run(("git", "checkout", "-b", "drift-remediation"))
    sh.run(("git", "commit", "-m", "changes made out of band"))

    sh.run(("git", "remote", "update"))
    sh.run(("git", "rebase", f"origin/{branch}"))
    sh.run(("git", "push", "origin", f"drift-remediation:{branch}"))

    pr.approve()

    sh.banner("user merges and closes pr")
    since = pr.add_label(":taco::apply")
    assert pr.check("tacos_apply").wait(since).success

    pr.merge()


@pytest.mark.xfail(raises=XFailed)
def test_roll_back(slices: Slices) -> None:
    since = create_drift(slices)

    sh.banner("re-apply from main branch")
    sh.run(("git", "remote", "update"))
    sh.run(("git", "reset", "--hard", "origin/main"))
    tf.apply(slices.workdir)

    sh.banner("request unlock")
    try:
        pr = tacos_demo.PR.wait_for("tacos/drift", since, timeout=6)
    except wait.TimeoutExpired:
        raise XFailed("tacos/drift branch not created")

    since = pr.add_label(":taco::unlock")
    assert pr.check("tacos_unlock").wait(since).success
    assert "INFO: Main branch clean, unlock successful." in pr.comments(
        since=since
    )
