from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Self

import lib.parse
from lib import json
from lib.json import assert_dict_of_strings
from lib.sh import sh

from .types import URL
from .types import CheckName
from .types import Generator


@dataclass(frozen=True, order=True)
class CheckRun:
    # NOTE: we want chronological ordering
    started_at: datetime  # 2023-11-29T22:44:24Z
    completed_at: datetime | None  # 2023-11-29T22:44:34Z
    url: URL  # https://github.com/getsentry/tacos-gha.test/actions/runs/7039437133/job/19158411914

    # variable-length strings last, for neatness
    name: CheckName  # tacos-gha / tacos_unlock (slice/...)
    status: str  # QUEUED, IN_PROGRESS, COMPLETED
    conclusion: str  # SUCCESS, FAILURE, NEUTRAL
    workflow: str  # Terraform Unlock

    @classmethod
    def from_json(cls, json: json.Value) -> Self:
        # example:
        # {
        #   "__typename": "CheckRun",
        #   "startedAt": "2023-11-29T22:44:24Z",
        #   "completedAt": "2023-11-29T22:44:34Z",
        #   OR  "completedAt": "0001-01-01T00:00:00Z"
        #   "conclusion": "SUCCESS",
        #   "detailsUrl": "https://github.com/getsentry/tacos-gha.test/actions/runs/7039437133/job/19158411914",
        #   "name": "tacos-gha / tacos_unlock",
        #   "status": "COMPLETED",
        #   "workflowName": "Terraform Unlock"
        # }
        attrs = assert_dict_of_strings(json).copy()
        assert attrs["__typename"] == "CheckRun", attrs
        del attrs["__typename"]

        tmp = datetime.fromisoformat(attrs.pop("completedAt"))
        if tmp.year == 1:
            completed_at = None
        else:
            completed_at = tmp

        return cls(
            started_at=datetime.fromisoformat(attrs.pop("startedAt")),
            completed_at=completed_at,
            url=attrs.pop("detailsUrl"),
            workflow=attrs.pop("workflowName"),
            **attrs,
        )

    @property
    def success(self) -> bool:
        return (self.status, self.conclusion) == ("COMPLETED", "SUCCESS")

    @property
    def failure(self) -> bool:
        return (self.status, self.conclusion) == ("COMPLETED", "FAILURE")

    @property
    def skipped(self) -> bool:
        return (self.status, self.conclusion) == ("COMPLETED", "NEUTRAL")

    @property
    def completed(self) -> bool:
        if self.status == "COMPLETED":
            assert self.completed_at, self.completed_at
            return True
        else:
            assert not self.completed_at, self.completed_at
            return False

    @property
    def relevance(self) -> tuple[object, ...]:
        """(attempt to) enable sorting by relevance to debugging"""
        result: list[object] = []

        # failures and incomplete jobs _must_ show up before successes
        result.append(
            ("NEUTRAL", "SUCCESS", "", "FAILURE").index(self.conclusion)
        )
        result.append(
            ("COMPLETED", "QUEUED", "IN_PROGRESS").index(self.status)
        )
        result.append(-self.started_at.timestamp())
        if self.completed_at:
            result.append(-self.completed_at.timestamp())
        else:
            result.append(0)
        result.append(self.name)
        return tuple(result)

    def __str__(self) -> str:
        format = "{workflow} / {name}: {started_at}-{completed_at} {status}({conclusion})"
        return format.format_map(vars(self))

    @property
    def job(self) -> str:
        return lib.parse.after(self.name, " / ")


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
