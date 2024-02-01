from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from lib import wait
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
    name: CheckName | None

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
                    self.name is None
                    or run.name == self.name
                    or run.job.startswith(self.name)
                )
            ):
                buckets[run.name].append(run)

        for _, runs in sorted(buckets.items()):
            run = max(runs)
            sh.info(run)
            yield run

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
        self, since: datetime | None = None, timeout: int = wait.WAIT_LIMIT
    ) -> CheckRun:
        """Wait for a check to run."""
        __tracebackhide__ = True

        if since is None:
            since = self.pr.since

        sh.info(f"waiting for {self} (since {since})...")

        result = wait.for_(lambda: self.ran(since), timeout=timeout)

        sh.banner(f"{self} ran")
        return result

    def __str__(self) -> str:
        if self.name:
            return f"{self.workflow} / {self.name}"
        else:
            return self.workflow
