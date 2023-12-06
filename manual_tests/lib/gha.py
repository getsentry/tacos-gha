from __future__ import annotations

from datetime import datetime
from typing import Iterable
from typing import cast

from lib import sh
from lib import wait

Check = dict[str, object]
CheckName = str


def get_checks() -> Iterable[object]:
    """get the most recent run of the named check"""
    return sh.jq(
        (
            "gh",
            "pr",
            "status",
            "--json",
            "statusCheckRollup",
            "--jq",
            # TODO: where are these fields documented??
            ".currentBranch.statusCheckRollup[]",
        )
    )


def show_check(check: Check) -> None:
    # example:
    # {
    #   "__typename": "CheckRun",
    #   "completedAt": "2023-11-29T22:44:34Z",
    #   "conclusion": "SUCCESS",
    #   "detailsUrl": "https://github.com/getsentry/tacos-gha.test/actions/runs/7039437133/job/19158411914",
    #   "name": "terraform_unlock",
    #   "startedAt": "2023-11-29T22:44:24Z",
    #   "status": "COMPLETED",
    #   "workflowName": "Terraform Unlock"
    # }
    format = "{name}: {startedAt}-{completedAt} {status}({conclusion})"
    sh.info(format.format_map(check))


def assert_ran(check: CheckName, since: datetime) -> None:
    """success if a specified github-actions job ran"""
    c = get_check(check)
    completed_at = c["completedAt"]
    assert isinstance(completed_at, str), completed_at

    completed_at = datetime.fromisoformat(completed_at)
    assert completed_at > since, (completed_at, since)


def get_check(check: CheckName) -> Check:
    """Return the _most recent_ status of the named check."""
    checks: list[Check] = []
    for c in get_checks():
        assert isinstance(c, dict), (type(c), c)

        assert isinstance(c["name"], str), c
        name: str = c["name"]
        if name == check:
            # https://github.com/microsoft/pyright/discussions/6577
            checks.append(cast(Check, c))

    if checks:
        checks.sort(  # chronological order
            key=lambda check: (check["startedAt"], check["completedAt"])
        )
        if len(checks) > 1:
            sh.info("multiple matching checks:", len(checks))
        for c in checks:
            show_check(c)

        return checks[-1]
    else:
        raise AssertionError(f"No such check found: {check}")


def assert_success(check: CheckName) -> None:
    # success if a specified github-actions job ran
    _check = get_check(check)
    assert _check["conclusion"] == "SUCCESS", _check


def assert_eventual_success(check: CheckName, since: datetime) -> None:
    sh.info(f"waiting for {check} (since {since})...")
    wait.for_(lambda: assert_ran(check, since))
    sh.banner(f"{check} ran")
    assert_success(check)
    sh.banner(f"{check} succeeded")
