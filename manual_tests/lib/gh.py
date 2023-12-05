from __future__ import annotations

from datetime import datetime

from lib import sh
from lib import wait
from lib.functions import now
from manual_tests.lib import gha

# FIXME: use a more specific type than str
URL = str
Branch = str


def assert_matching_comment(comment: str, since: datetime) -> None:
    # Fetch the comments on the PR
    comments = sh.jq(
        (
            "gh",
            "pr",
            "view",
            "--json",
            "comments",
            "--jq",
            ".comments.[] | {body, createdAt}",
        ),
        encoding="UTF-8",
    )

    # Parse the comments and their creation times
    for c in comments:
        assert isinstance(c, dict), c

        assert isinstance(c["createdAt"], str), c
        created_at = datetime.fromisoformat(c["createdAt"])

        if created_at >= since:
            if comment in c["body"]:
                return
    else:
        raise AssertionError(f"No matching comment: {comment}\n{comments}")


def assert_pr_has_label(pr_url: URL, label: str) -> None:
    sh.banner("asserting PR has label:")
    labels = sh.stdout(
        (
            "gh",
            "pr",
            "view",
            "--json",
            "labels",
            "--jq",
            ".labels.[] | .name",
            pr_url,
        )
    )

    assert label in labels, (label, labels)


def assert_pr_is_approved(pr_url: URL) -> None:
    sh.banner("asserting PR is approved:")
    # TODO: actually check that the PR is approved (once we add a second service account)
    assert_pr_has_label(pr_url, ":taco::approve")


def open_pr(branch: Branch) -> str:
    return sh.stdout(("gh", "pr", "create", "--fill-first", "--head", branch))


def close_pr(pr_url: URL) -> None:
    sh.banner("cleaning up:")
    since = now()

    if sh.success(("gh", "pr", "edit", "--add-label", ":taco::unlock")):
        sh.banner("waiting for unlock...")
        wait.for_(lambda: gha.assert_ran("terraform_unlock", since))
        sh.banner("unlocked.")

    sh.banner("deleting branch:")
    sh.run(
        (
            "gh",
            "pr",
            "close",
            "--comment",
            "test cleanup",
            "--delete-branch",
            pr_url,
        )
    )


def approve_pr(pr_url: URL) -> None:
    sh.banner("approving PR:")
    # TODO: find a way to approve with a separate service account
    add_label(pr_url, ":taco::approve")


def add_label(pr_url: URL, label: str) -> None:
    sh.banner(f"adding label {label} to PR:")
    sh.run(("gh", "pr", "edit", "--add-label", label, pr_url))
