from __future__ import annotations

from datetime import datetime
from typing import Iterable

from lib import json
from lib import sh
from lib import wait

from .gh import PR
from .gha_check import Check as Check

# TODO: centralize reused type aliases
CheckName = str


def get_checks(pr: PR) -> Iterable[json.Value]:
    """get the most recent run of the named check"""
    return sh.jq(
        (
            "gh",
            "pr",
            "view",
            pr.url,
            "--json",
            "statusCheckRollup",
            "--jq",
            # TODO: where are these fields documented??
            ".statusCheckRollup[]",
        )
    )


def assert_ran(
    pr: PR, check_name: CheckName, since: datetime | None = None
) -> None:
    """success if a specified github-actions job ran"""
    c = get_check(pr, check_name)
    if since is None:
        since = pr.since

    assert c.completedAt > since, (c, since)


def get_check(pr: PR, check_name: CheckName) -> Check:
    """Return the _most recent_ status of the named check."""
    checks: list[Check] = []
    for obj in get_checks(pr):
        check = json.assert_dict_of_strings(obj)
        if check["name"] == check_name:
            # https://github.com/microsoft/pyright/discussions/6577
            checks.append(Check.from_json(check))

    if checks:
        checks.sort(  # chronological order
            key=lambda check: (check.startedAt, check.completedAt)
        )
        if len(checks) > 1:
            sh.info("multiple matching checks:", len(checks))
        for c in checks:
            sh.info(c)

        return checks[-1]
    else:
        raise AssertionError(f"No such check found: {check_name}")


def assert_success(pr: PR, check_name: CheckName) -> None:
    # success if a specified github-actions job ran
    check = get_check(pr, check_name)
    assert check.conclusion == "SUCCESS", check


def assert_eventual_success(
    pr: PR, check_name: CheckName, since: datetime | None = None
) -> None:
    if since is None:
        since = pr.since
    sh.info(f"waiting for {check_name} (since {since})...")
    wait.for_(lambda: assert_ran(pr, check_name, since))
    sh.banner(f"{check_name} ran")
    assert_success(pr, check_name)
    sh.banner(f"{check_name} succeeded")
