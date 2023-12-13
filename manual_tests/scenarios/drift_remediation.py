#!/usr/bin/env py.test
from __future__ import annotations

from datetime import datetime

from lib.functions import now
from lib.sh import sh
from manual_tests.lib import tacos_demo
from manual_tests.lib import tf
from manual_tests.lib.gh import workflow
from manual_tests.lib.slice import Slices


def setup(slices: Slices) -> datetime:
    sh.banner("somebody changes infrastructure out of band")
    repo = tacos_demo.clone()
    with sh.cd(repo):
        for slice in slices:
            slice.edit()
        tf.apply()

    sh.banner("pretend an hour passed: trigger the drift-scan job")
    since = now()
    workflow.run("terraform_detect_drift.yml")
    return since


def test_roll_forward(slices: Slices, test_name: str) -> None:
    since = setup(slices)

    sh.banner("check out automatically-created PR")
    pr = tacos_demo.PR.wait_for("tacos/drift", since, slices=slices)

    sh.banner("commit out-of-band changes so plan is clean")
    try:
        # Cleanup: roll back the infrastructure changes
        sh.run(("git", "remote", "update"))
        branch = "tacos/drift"
        sh.run(("git", "checkout", branch))
        tacos_demo.commit(branch, test_name, "changes made out of band")

        sh.banner("user merges and closes pr")
        pr.approve()
        pr.merge()
    finally:
        pr.close()


def test_roll_back(pr: tacos_demo.PR, slices: Slices, test_name: str) -> None:
    setup(slices)

    sh.banner("re-apply from main branch")
    tacos_demo.clone()

    try:
        # Cleanup: roll back the infrastructure changes
        sh.run(("git", "remote", "update"))
        branch = "tacos/drift"
        sh.run(("git", "checkout", branch))
        tacos_demo.commit(branch, test_name, "changes made out of band")
        tf.apply()

        sh.banner("edit and/or apply till plan is clean")
        sh.banner("request unlock")
    finally:
        pr.close()
