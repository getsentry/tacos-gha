#!/usr/bin/env python3.12
from __future__ import annotations

from lib import json
from lib import wait
from lib.functions import one
from lib.parse import Parse
from lib.sh import sh
from lib.types import URL
from lib.user_error import UserError

JOB = "conflict-detection"
TAG = f'<!-- getsentry/tacos-gha "{JOB}" -->'
MERGE_CONFLICT_MESSAGE = f"""\
You currently have a merge conflict, which prevents github-actions from running
any checks. TACOS will resume doing terraform stuff for you once the conflict is
resolved.
{TAG}
"""

# mypy can't find LessThanOneError
# mypy: ignore-errors


def pr_conflict_status(pr_url: URL) -> str:
    pr = sh.json(("gh", "pr", "view", pr_url, "--json=state,mergeStateStatus"))
    state = json.get(pr, str, "state")
    if state in ("MERGED", "CLOSED"):
        return state
    else:
        return json.get(pr, str, "mergeStateStatus")


def tell_user(pr_url: URL) -> None:
    sh.run(
        ("gh", "pr", "comment", pr_url, "--body-file", "-"),
        input=MERGE_CONFLICT_MESSAGE,
    )


def find_conflict_message(pr_url: URL) -> int | None:
    result: set[int] = set()
    for comment in sh.jq(
        ("gh", "pr", "view", pr_url, "--json=comments", "--jq=.comments[]")
    ):
        body = json.get(comment, str, "body")

        if TAG in body:
            # the api doesn't want the id seen here (IC_kwDOKu2SPc50T-Ws)
            # it wants the numeric id from the url (...#issuecomment-1951393358)
            url = json.get(comment, str, "url")
            id = Parse(url).after.last("-")
            result.add(int(id))

    if result:
        return one(result)
    else:
        return None


def get_owner_repo(pr_url: str) -> tuple[str, str]:
    # https://github.com/getsentry/tacos-gha.demo/pull/1635
    netloc, owner, repo, pull_endpoint, pull = pr_url.rsplit("/", 4)

    assert netloc == "https://github.com", netloc
    assert pull_endpoint == "pull", pull_endpoint
    assert pull.isdigit(), pull

    return owner, repo


def delete_message(pr_url: str, comment_id: int) -> None:
    # I could only find how to do this via `gh api` which is considerably harder
    # to use. Please update if you find a more straightforward way.
    owner, repo = get_owner_repo(pr_url)

    # https://docs.github.com/en/rest/issues/comments#delete-an-issue-comment
    endpoint = f"/repos/{owner}/{repo}/issues/comments/{comment_id}"

    sh.run(("gh", "api", "-X", "DELETE", endpoint))


def tacos_conflict_detection(pr_url: URL) -> None:
    def pr_conflict_status_known() -> str | None:
        status = pr_conflict_status(pr_url)
        sh.debug("PR merge status:", status)
        if status == "UNKNOWN":
            return None  # keep waiting
        else:
            return status

    status = wait.for_(pr_conflict_status_known)
    prior_message = find_conflict_message(pr_url)

    if status == "DIRTY":
        sh.debug("PR is merge-conflicted.")
        if prior_message is None:
            tell_user(pr_url)
        else:
            sh.debug(f"Owner already notified. (comment {prior_message})")
        sh.run(("gh", "pr", "edit", pr_url, "--add-label=:taco::conflict"))
    else:
        sh.debug("PR is merge-clean.")
        if prior_message:
            delete_message(pr_url, prior_message)
        else:
            sh.debug("No stale notification to be removed.")
        sh.run(("gh", "pr", "edit", pr_url, "--remove-label=:taco::conflict"))


@UserError.handler
def main() -> None:
    from sys import argv

    tacos_conflict_detection(URL(argv[1]))


if __name__ == "__main__":
    raise SystemExit(main())
