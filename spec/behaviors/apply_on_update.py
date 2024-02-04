#!/usr/bin/env py.test
from __future__ import annotations

from typing import Callable

from spec.lib import tacos_demo
from spec.lib.slice import Slices

TEST_NAME = __name__

from pytest import fixture

from lib.parse import Parse


@fixture
def slices_cleanup() -> Callable[[Slices], None]:
    return Slices.force_clean


def test(pr: tacos_demo.PR) -> None:
    pr.approve()
    assert pr.is_approved()

    # the taco-apply label causes the plan to become clean:
    assert not pr.slices.plan_is_clean()
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

        assert "$ tf-lock-acquire .\ntf-lock-acquire: success: .(" in commands
        # the next bit is github-username@fake-pr-domain, which seems tricky

        assert """\
$ sudo-gcp terragrunt run-all init
You are authenticated for the next hour as: tacos-gha-tf-apply@sac-dev-sa.iam.gserviceaccount.com
""" in commands

        assert "tf-lock-release" not in commands

        for command in (
            f"cd {pr.slices.subpath}/{slice}",
            f"sudo-gcp tf-lock-acquire",
            f"sudo-gcp terragrunt run-all init",
            f"sudo-gcp terragrunt run-all refresh",
            f"sudo-gcp terragrunt run-all apply --auto-approve",
        ):
            line = f"\n$ {command}\n"
            assert line in commands
            commands = commands.after.first(line)
