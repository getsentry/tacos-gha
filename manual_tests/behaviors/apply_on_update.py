#!/usr/bin/env py.test
from __future__ import annotations

from pathlib import Path

import pytest

from manual_tests.lib import tacos_demo
from manual_tests.lib import tf

TEST_NAME = __name__


def test(pr: tacos_demo.PR, workdir: Path) -> None:
    assert pr.check("terraform_lock").wait().success

    pr.approve()
    assert pr.approved()

    # the taco-apply label causes the plan to become clean:
    assert tf.plan_dirty(workdir)
    since = pr.add_label(":taco::apply")
    assert pr.check("terraform_apply").wait(since).success
    assert tf.plan_clean(workdir)
