from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from lib import json
from lib import wait
from lib.sh import sh

from .types import URL
from .types import CheckName
from .types import Generator

if TYPE_CHECKING:
    from .check_run import CheckRun
    from .pr import PR


class DidNotRun(Exception):
    pass


def get_runs_json(pr_url: URL) -> Generator[json.Value]:
    """Get the json of all runs, for the named check."""
    # https://docs.github.com/en/graphql/reference/objects#statuscheckrollup
    return sh.jq(
        (
            "gh",
            "pr",
            "view",
            pr_url,
            "--json",
            "statusCheckRollup",
            "--jq",
            ".statusCheckRollup[]",
        )
    )


@dataclass(frozen=True)
class Check:
    pr: PR
    name: CheckName

    def get_runs(self) -> Generator[CheckRun]:
        """Return the all runs of this check."""
        from .check_run import CheckRun

        for obj in get_runs_json(self.pr.url):
            run = CheckRun.from_json(obj)
            if run.name == self.name:
                yield run

    def latest(self) -> CheckRun:
        """Return the _most recent_ status of the named check."""
        result = max(self.get_runs(), default=None)
        if result is None:
            raise AssertionError(f"Check didn't run: {self}")

        sh.info(result)
        return result

    def assert_ran(self, since: datetime) -> CheckRun:
        """Did a specified github-actions job run, lately?"""
        c = self.latest()
        assert c.completedAt > since
        return c

    def assert_not_ran(self, since: datetime) -> None:
        """Did a specified github-actions job not run, lately?"""
        try:
            self.assert_ran(since)
        except AssertionError:
            return
        raise AssertionError(f"Check ran: {self}")

    def wait(
        self, since: datetime | None = None, timeout: int = wait.WAIT_LIMIT
    ) -> CheckRun:
        """Wait for a check to run."""
        if since is None:
            since = self.pr.since
        sh.info(f"waiting for {self.name} (since {since})...")
        result = wait.for_(lambda: self.assert_ran(since), timeout=timeout)
        sh.banner(f"{self.name} ran")
        return result
