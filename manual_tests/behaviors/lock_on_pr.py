#!/usr/bin/env py.test
from __future__ import annotations

from manual_tests.lib import tacos_demo


def test(pr: tacos_demo.PR) -> None:
    for slice in pr.slices:
        assert (
            pr.check("Terraform Lock", f"tacos-gha / main ({slice})")
            .wait()
            .success
        )
    pr.slices.assert_locked()
