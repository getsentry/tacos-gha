from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING
from typing import Self
from typing import Sequence

from lib import json
from lib.functions import now
from lib.sh import sh
from lib import wait

from .types import URL
from .types import Branch
from .types import CheckName
from .types import Label

Comment = str  # a PR comment

if TYPE_CHECKING:
    from .check import Check


@dataclass(frozen=True)
class PR:
    branch: Branch
    url: URL
    since: datetime

    @classmethod
    def open(cls, branch: Branch, **attrs: object) -> Self:
        since = now()
        url = sh.stdout(
            ("gh", "pr", "create", "--fill-first", "--head", branch)
        )
        return cls(branch, url, since, **attrs)

    def close(self) -> None:
        sh.banner("cleaning up:")
        since = now()

        if sh.success(("gh", "pr", "edit", "--add-label", ":taco::unlock")):
            sh.banner("waiting for unlock...")
            self.check("terraform_unlock").wait(since)
            sh.banner("unlocked.")

        sh.banner("deleting branch:")
        sh.run(
            (
                "gh",
                "pr",
                "close",
                "--comment",
                "test cleanup",
                "--delete-branch",
                self.url,
            )
        )

    def approve(self) -> None:
        sh.banner("approving PR:")
        # TODO: find a way to approve with a separate service account
        self.add_label(":taco::approve")

    def approved(self) -> bool:
        # TODO: use a separate service account to approve the PR
        # TODO: actually check that the PR is approved
        return ":taco::approve" in self.labels()

    def add_label(self, label: Label) -> None:
        sh.banner(f"adding label {label} to PR:")
        sh.run(("gh", "pr", "edit", "--add-label", label, self.url))

    def merge_pr(self) -> str:
        return sh.stdout(("gh", "pr", "merge", "--squash", "--auto", self.url))

    def labels(self) -> Sequence[Label]:
        result: list[Label] = []
        for label in sh.lines(
            (
                "gh",
                "pr",
                "view",
                "--json",
                "labels",
                "--jq",
                ".labels.[] | .name",
                self.url,
            )
        ):
            result.append(label)
        return tuple(result)

    def comments(self, since: datetime) -> Sequence[Comment]:
        # Fetch the comments on the PR
        comments = sh.jq(
            (
                "gh",
                "pr",
                "view",
                "--json",
                "comments",
                "--jq",
                ".comments.[] | {body, createdAt}",
            ),
            encoding="UTF-8",
        )

        # Parse the comments and their creation times
        result: list[Comment] = []
        for comment in comments:
            comment = json.assert_dict_of_strings(comment)
            created_at = datetime.fromisoformat(comment["createdAt"])

            if created_at >= since:
                result.append(comment["body"])
        return tuple(result)

    def check(self, check_name: CheckName) -> Check:
        from .check import Check

        return Check(self, check_name)

    @classmethod
    def from_branch(cls, branch: Branch, since: datetime) -> Self:
        url = sh.stdout(("gh", "pr", "view", "--json", "url", branch))
        return cls(branch, url, since)


    @classmethod
    def wait_for_pr(cls, branch: str, since: datetime, timeout: int = 150) -> PR:
        def branch_pr() -> PR:
            assert sh.success(("gh", "pr", "view", branch))
            return PR.from_branch(branch, since)
        
        return wait.for_(branch_pr, timeout=timeout, sleep=5)
