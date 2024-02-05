#!/usr/bin/env py.test
from __future__ import annotations

from lib.parse import Parse
from spec.lib import tacos_demo


def test(pr: tacos_demo.PR) -> None:
    assert pr.check("Terraform Plan").wait().success
    pr.slices.assert_locked()

    since = pr.add_label(":taco::unlock")
    assert pr.check("Terraform Unlock").wait(since).success
    pr.slices.assert_unlocked()

    unlock_comments = pr.get_comments_for_job("unlock", since)
    assert set(unlock_comments) == pr.slices.slices

    for slice, comment in sorted(unlock_comments.items()):
        assert (
            Parse(comment).before.first("\n")
            == f"### TACOS Unlock: {pr.slices.subpath}/{slice}"
        )

        assert "\nTerraform state has been successfully unlocked!\n" in comment

        assert "<summary>tf-lock-release: success: .(" in comment
        # the next bit is github-username@fake-pr-domain, which seems tricky
