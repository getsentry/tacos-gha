from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING
from typing import Self
from typing import Sequence

from lib import json
from lib import wait
from lib.functions import now
from lib.functions import one
from lib.sh import sh

from .types import URL
from .types import Branch
from .types import CheckName
from .types import Label

Comment = str  # a PR comment

if TYPE_CHECKING:
    from .check import Check

# mypy: disable-error-code="type-var, misc"
# we should find a better way to denote tf-plan in comments
PLAN_MESSAGE = (
    '<summary>Execution result of "run-all plan -out plan" in "."</summary>'
)


@dataclass(frozen=True)
class PR:
    branch: Branch
    url: URL
    since: datetime

    @classmethod
    def open(cls, branch: Branch, draft: bool = False, **attrs: object) -> Self:
        since = now()
        command = list(("gh", "pr", "create", "--fill-first", "--head", branch))
        if draft:
            command.append("--draft",)
        url = sh.stdout(tuple(command))
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

    def get_plan(self, since: datetime | None = None) -> str:
        """Return the body of the github PR comment containing the tf plan."""
        if since is None:
            since = self.since

        assert self.check("terraform_plan").wait(since).success
        plan = [
            comment
            for comment in self.comments(since)
            if PLAN_MESSAGE in comment
        ]
        # there should be just one plan in that timeframe
        return one(plan)

    def merge(self) -> str:
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
    def wait_for_pr(
        cls, branch: str, since: datetime, timeout: int = 60
    ) -> Self:
        # mypy doesn't understand closures :(
        def branch_pr() -> Self:
            assert sh.success(("gh", "pr", "view", branch))
            return cls.from_branch(branch, since)

        return wait.for_(branch_pr, timeout=timeout, sleep=5)
