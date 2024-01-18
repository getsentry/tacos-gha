#!/usr/bin/env py.test
from __future__ import annotations

from lib.types import Path
from manual_tests.lib import tacos_demo
from manual_tests.lib import tf

TEST_NAME = __name__


def test(pr: tacos_demo.PR, slices_subpath: Path) -> None:
    # cleanup: apply main in case some other test left things in a dirty state
    # TODO: move to a fixture?
    tf.apply(pr.slices.workdir / slices_subpath)

    pr.approve()
    assert pr.approved()

    slices_dir = pr.slices.workdir / slices_subpath

    # the taco-apply label causes the plan to become clean:
    assert tf.plan_dirty(slices_dir)
    since = pr.add_label(":taco::apply")
    assert pr.check("Terraform Apply").wait(since).success
    assert tf.plan_clean(slices_dir)
