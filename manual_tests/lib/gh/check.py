from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from lib import wait
from lib.sh import sh

from .types import CheckName
from .types import Generator

if TYPE_CHECKING:
    from .check_run import CheckRun
    from .pr import PR


class DidNotRun(Exception):
    pass


@dataclass(frozen=True)
class Check:
    pr: PR
    name: CheckName

    def latest(self, since: datetime) -> Generator[CheckRun]:
        """Return the _most recent_ status of the named check."""
        __tracebackhide__ = True

        buckets: defaultdict[str, list[CheckRun]] = defaultdict(list)
        for run in self.pr.get_check_runs(since):
            if run.started > since and run.job.startswith(self.name):
                buckets[run.name].append(run)

        for _, runs in sorted(buckets.items()):
            run = max(runs)
            sh.info(run)
            yield run

    def ran(self, since: datetime) -> tuple[CheckRun, ...]:
        """Did a specified github-actions job run, lately?"""
        __tracebackhide__ = True

        runs = tuple(self.latest(since))
        if runs:
            sh.banner(runs[0].url)

        if all(run.completed > run.started for run in runs):
            return runs
        else:
            sh.debug("not finished yet")
            return ()

    def wait(
        self, since: datetime | None = None, timeout: int = wait.WAIT_LIMIT
    ) -> CheckRun:
        """Wait for a check to run."""
        __tracebackhide__ = True

        if since is None:
            since = self.pr.since

        sh.info(f"waiting for {self} (since {since})...")

        result = wait.for_(lambda: self.ran(since), timeout=timeout)

        sh.banner(f"{self} ran")
        return max(result, key=lambda run: run.relevance)

    def __str__(self) -> str:
        return self.name
