from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from lib import json
from lib import wait
from lib.sh import sh

from .check_run import CheckRun
from .pr import PR
from .types import URL
from .types import CheckName
from .types import Generator


class DidNotRun(Exception):
    pass


@dataclass(frozen=True)
class Check:
    pr: PR
    name: CheckName

    def get_run(self, since: datetime | None = None) -> CheckRun:
        """Did a specified github-actions job run, lately?"""
        c = self.get_latest()
        if since is None:
            since = self.pr.since

        if c.completedAt > since:
            return c
        else:
            raise DidNotRun(self)

    def get_runs(self) -> Generator[CheckRun]:
        """Return the all runs of this check."""
        for obj in get_runs_json(self.pr.url):
            run = CheckRun.from_json(obj)
            if run.name == self.name:
                yield run

    def get_latest(self) -> CheckRun:
        """Return the _most recent_ status of the named check."""
        result = max(self.get_runs(), default=None)
        sh.info(result)

        if result is not None:
            return result
        else:
            raise AssertionError(f"No such check found: {self.name}")

    def wait(
        self, since: datetime | None = None, timeout: int | None = None
    ) -> CheckRun:
        """Wait for a check to run."""
        if since is None:
            since = self.pr.since
        sh.info(f"waiting for {self.name} (since {since})...")
        result = wait.for_(lambda: self.get_run(since), timeout=timeout)
        sh.banner(f"{self.name} ran")
        return result


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
