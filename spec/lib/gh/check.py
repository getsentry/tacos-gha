from __future__ import annotations

import dataclasses
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from lib import wait
from lib.functions import now
from lib.sh import sh

from .types import CheckName
from .types import Generator
from .types import WorkflowName

if TYPE_CHECKING:
    from .check_run import CheckRun
    from .pr import PR


class DidNotRun(Exception):
    pass


@dataclass(frozen=True)
class CheckFilter:
    pr: PR
    workflow: WorkflowName
    check: CheckName | None

    def latest(self, since: datetime) -> Generator[CheckRun]:
        """Return the _most recent_ status of the named check."""
        __tracebackhide__ = True

        buckets: defaultdict[str, list[CheckRun]] = defaultdict(list)
        for run in self.pr.get_check_runs(since):
            if (
                True
                and run.started_at > since
                and run.workflow == self.workflow
                and (
                    self.check is None
                    or run.name == self.check
                    or run.job.startswith(self.check)
                )
            ):
                buckets[run.name].append(run)

        for _, runs in sorted(buckets.items()):
            run = max(runs)
            sh.info(run)
            yield run

    def exists(self, since: datetime) -> CheckRun | None:
        """Does such a thing exist, at all?"""
        __tracebackhide__ = True

        filter = dataclasses.replace(self, check=None)

        runs = tuple(filter.latest(since))
        if not runs:
            return None

        run = max(runs, key=lambda run: run.relevance)
        sh.banner(run.url)
        return run

    def ran(self, since: datetime) -> CheckRun | None:
        """Did a specified github-action run, lately?"""
        __tracebackhide__ = True

        runs = tuple(self.latest(since))
        if not runs:
            return None

        run = max(runs, key=lambda run: run.relevance)
        sh.banner(run.url)
        if run.completed:  # all runs completed, or else one failed
            return run
        else:
            return None

    def wait(
        self, since: datetime | None = None, timeout: float = wait.WAIT_LIMIT
    ) -> CheckRun:
        """Wait for a check to run."""
        __tracebackhide__ = True

        if since is None:
            since = self.pr.since

        start = now()
        sh.info(f"waiting for {self} (since {since})...")

        # use a shorter timeout just to check that such a thing exists
        timeout_exists = min(30, timeout)
        wait.for_(lambda: self.exists(since), timeout=timeout_exists)

        # use the rest of the timeout to wait for run
        time_used = now() - start
        timeout_run = timeout - time_used.total_seconds()
        result = wait.for_(lambda: self.ran(since), timeout=timeout_run)

        sh.banner(f"{self} ran")
        return result

    def __str__(self) -> str:
        if self.check:
            return f"{self.workflow} / {self.check}"
        else:
            return self.workflow
