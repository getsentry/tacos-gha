from __future__ import annotations

from datetime import datetime

from lib import json
from lib import wait
from lib.sh import sh

from .gh import PR
from .gha_check import Check as Check

# TODO: centralize reused type aliases
CheckName = str


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
    for obj in pr.checks():
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


def wait_for_check(pr: PR, check: CheckName, since: datetime) -> Check:
    sh.info(f"waiting for {check}...")
    wait.for_(lambda: assert_ran(pr, check, since))
    sh.banner(f"{check} ran")
    return get_check(pr, check)


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
