#!/usr/bin/env py.test
from __future__ import annotations

from typing import Callable

from pytest import fixture

from lib.parse import Parse
from spec.lib import tacos_demo
from spec.lib.slice import Slices
from spec.lib.testing import assert_sequence_in_log


@fixture
def slices_cleanup() -> Callable[[Slices], None]:
    return Slices.force_clean


def test(pr: tacos_demo.PR) -> None:
    pr.approve()
    assert pr.is_approved()

    # the taco-apply label causes the plan to become clean (and locked):
    assert not pr.slices.plan_is_clean()
    pr.slices.assert_unlocked()

    since = pr.add_label(":taco::apply")
    assert pr.check("Terraform Apply").wait(since).success
    assert pr.slices.plan_is_clean()

    comments = pr.get_comments_for_job("apply", since)
    assert set(comments) == pr.slices.slices

    for slice, comment in sorted(comments.items()):
        assert (
            Parse(comment).before.first("\n")
            == f"### TACOS Apply: {pr.slices.subpath}/{slice}"
        )

        summary = (
            Parse(comment).after.first("<summary>").before.first("</summary>")
        )
        assert summary.startswith("Apply complete! Resources: ")
        # ... X added, Y changed, Z ...
        assert summary.endswith(" destroyed.")

        assert "<summary>Commands: (success)</summary>" in comment

        commands: Parse = (
            Parse(comment).after.last("</summary>").before.first("</details>")
        )

        assert_sequence_in_log(
            commands,
            (
                f"\n$ cd {pr.slices.subpath}/{slice}\n",
                """
$ sudo-gcp tf-lock-acquire
You are authenticated for the next hour as: tacos-gha-tf-apply@sac-dev-sa.iam.gserviceaccount.com

$ tf-lock-info .

$ terragrunt --terragrunt-no-auto-init=false validate-inputs

$ terragrunt --terragrunt-no-auto-init=false terragrunt-info

$ tf-lock-info .
tf-lock-acquire: success: """,  # the next bit is github-username@fake-pr-domain, which seems tricky
                """
$ sudo-gcp terragrunt run-all init
You are authenticated for the next hour as: tacos-gha-tf-apply@sac-dev-sa.iam.gserviceaccount.com
""",
                "\nTerraform has been successfully initialized!\n",
                "\n$ sudo-gcp terragrunt run-all refresh\n",
                "\n$ sudo-gcp terragrunt run-all apply --auto-approve\n",
            ),
        )

        # lock should continue to be held
        assert "tf-lock-release" not in commands

        tf_result: Parse = Parse(comment).between("</details>", "</details>")
        assert "\nTerraform will perform the following actions:\n" in tf_result

    pr.slices.assert_locked()
