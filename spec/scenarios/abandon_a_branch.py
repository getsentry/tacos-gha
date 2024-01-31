#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib.sh import sh
from spec.lib import tacos_demo
from spec.lib.xfail import XFailed


@pytest.mark.xfail(raises=XFailed)
def test(pr: tacos_demo.PR) -> None:
    sh.banner("PR is approved and applied")
    pr.approve()
    assert pr.is_approved()

    since = pr.add_label(":taco::apply")
    assert pr.check("Terraform Apply").wait(since).success

    sh.banner("For various reasons, the PR is not merged. Time passes")
    # TODO: workflow to automatically add taco:stale label as appropriate
    since = pr.add_label(":taco::stale")

    sh.banner("An attempt is made to notify the PR owner")
    try:
        assert pr.check("notify_owner").wait(since, timeout=3).success
    except AssertionError:
        raise XFailed("notify_owner action does not exist")

    sh.banner("More time passes")
    # TODO: workflow to automatically add taco:abandoned label as appropriate
    since = pr.add_label(":taco::abandoned")

    sh.banner("An attempt is made to notify other users of the repo")
    assert pr.check("notify_collaborators").wait(since).success
