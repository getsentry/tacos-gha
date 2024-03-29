#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib import wait
from lib.parse import Parse
from spec.lib import tacos_demo
from spec.lib.gh import gh
from spec.lib.slice import Slice
from spec.lib.testing import assert_sequence_in_log


@pytest.fixture
def pr(pr: tacos_demo.PR, test_name: str) -> tacos_demo.PR:

    slices2 = pr.slices.with_some_overlap()
    branch, message = tacos_demo.edit_slices(
        slices2, test_name, message="more code"
    )

    since = gh.commit_and_push(branch, message)

    from dataclasses import replace

    return replace(pr, slices=pr.slices | slices2, since=since)


def test(pr: tacos_demo.PR) -> None:
    assert pr.check("Terraform Plan").wait().success

    def get_comments() -> dict[Slice, gh.Comment]:
        comments = pr.get_comments_for_job("plan")

        slices_found = frozenset(comments)
        assert pr.slices.slices == slices_found
        return comments

    comments = wait.for_(get_comments)

    for slice, comment in sorted(comments.items()):
        assert (
            Parse(comment).after.first("\n### ").before.first("\n")
            == f"{pr.slices.subpath}/{slice}"
        )

        summary = (
            Parse(comment).after.first("<summary>").before.first("</summary>")
        )
        assert summary.startswith("Plan: ")
        # ... X to add, Y to change, Z ...
        assert summary.endswith(" to destroy.")

        assert "<summary>Commands: (success, tfplan todo)</summary>" in comment

        commands: Parse = (
            Parse(comment).after.last("</summary>").before.first("</details>")
        )

        assert_sequence_in_log(
            commands,
            (
                f"\n$ cd {pr.slices.subpath}/{slice}\n",
                """\
$ sudo-gcp tf-lock-acquire
You are authenticated for the next hour as: tacos-gha-tf-state-admin@sac-dev-sa.iam.gserviceaccount.com
tf-lock-acquire: success: .(""",  # the next bit is github-username@fake-pr-domain, which seems tricky
                """\

$ sudo-gcp terragrunt run-all init
You are authenticated for the next hour as: tacos-gha-tf-state-admin@sac-dev-sa.iam.gserviceaccount.com
""",
                "\nTerraform has been successfully initialized!\n",
                "\n$ sudo-gcp terragrunt run-all refresh\n",
                "\n$ sudo-gcp terragrunt run-all plan -out $slice/tfplan\n",
            ),
        )

        # lock should continue to be held
        assert "tf-lock-release" not in commands

        tf_result: Parse = Parse(comment).between("</details>", "</details>")
        assert "\nTerraform will perform the following actions:\n" in tf_result

        assert tf_result.strip().endswith(
            """\
Saved the plan to:
tfplan

To perform exactly these actions, run the following command to apply:
    terraform apply "tfplan"
```"""
        )

    # lock should continue to be held
    pr.slices.assert_locked()
