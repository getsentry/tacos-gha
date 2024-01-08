from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Self

from lib import json
from lib.json import assert_dict_of_strings

from .types import URL
from .types import CheckName


@dataclass(frozen=True, order=True)
class CheckRun:
    # NOTE: we want chronological ordering
    started: datetime  # 2023-11-29T22:44:24Z
    completed: datetime  # 2023-11-29T22:44:34Z
    url: URL  # https://github.com/getsentry/tacos-gha.test/actions/runs/7039437133/job/19158411914

    # variable-length strings last, for neatness
    name: CheckName  # terraform_unlock
    status: str  # COMPLETED
    conclusion: str  # SUCCESS
    workflow: str  # Terraform Unlock

    @classmethod
    def from_json(cls, json: json.Value) -> Self:
        # example:
        # {
        #   "__typename": "CheckRun",
        #   "startedAt": "2023-11-29T22:44:24Z",
        #   "completedAt": "2023-11-29T22:44:34Z",
        #   "conclusion": "SUCCESS",
        #   "detailsUrl": "https://github.com/getsentry/tacos-gha.test/actions/runs/7039437133/job/19158411914",
        #   "name": "terraform_unlock",
        #   "status": "COMPLETED",
        #   "workflowName": "Terraform Unlock"
        # }
        attrs = assert_dict_of_strings(json).copy()
        assert attrs["__typename"] == "CheckRun", attrs
        del attrs["__typename"]
        return cls(
            started=datetime.fromisoformat(attrs.pop("startedAt")),
            completed=datetime.fromisoformat(attrs.pop("completedAt")),
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

    def __str__(self) -> str:
        format = (
            "{workflow} / {name}: {started}-{completed} {status}({conclusion})"
        )
        return format.format_map(vars(self))
