from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Self
from typing import Sequence

from lib import json
from lib import wait
from lib.functions import now
from lib.sh import sh
from lib.types import Generator
from manual_tests.lib.xfail import XFailed

from .types import URL
from .types import Branch
from .types import CheckName
from .types import Label

Comment = str  # a PR comment

if TYPE_CHECKING:
    from .check import Check

# mypy doesn't understand closures :(
# mypy: disable-error-code="type-var, misc"


@dataclass(frozen=True)
class PR:
    branch: Branch
    url: URL
    since: datetime

    @classmethod
    def open(cls, workdir: Path, branch: Branch, **attrs: object) -> Self:
        since = now()
        with sh.cd(workdir):
            url = sh.stdout(
                ("gh", "pr", "create", "--fill-first", "--head", branch)
            )
        return cls(branch, url, since, **attrs)

    @contextmanager
    @classmethod
    def opened(cls, workdir: Path, branch: Branch) -> Generator[Self]:
        pr = cls.open(workdir, branch)
        sh.banner("PR opened:", pr.url)
        yield pr
        pr.close()

    def close(self) -> None:
        sh.banner("deleting branch")
        sh.run(
            (
                "gh",
                "pr",
                "close",
                self.url,
                "--comment",
                "automatic test cleanup",
                "--delete-branch",
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
        sh.run(("gh", "pr", "edit", self.url, "--add-label", label))

    def merge(self) -> str:
        sh.banner("merging PR")
        try:
            result = sh.stdout(("gh", "pr", "merge", self.url, "--squash"))
        except sh.CalledProcessError:
            # + $ gh pr merge --squash https://github.com/getsentry/tacos-gha.demo/pull/363
            # X Pull request #363 is not mergeable: the base branch policy prohibits the merge.
            # To have the pull request merged after all the requirements have been met, add the `--auto` flag.
            # To use administrator privileges to immediately merge the pull request, add the `--admin` flag.
            raise XFailed("terraform changes not yet mergeable")
        else:
            raise AssertionError(
                f"this shouldn't work, yet... result: {result}"
            )

    def labels(self) -> Sequence[Label]:
        result: list[Label] = []
        for label in sh.lines(
            (
                "gh",
                "pr",
                "view",
                self.url,
                "--json",
                "labels",
                "--jq",
                ".labels.[] | .name",
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
                self.url,
                "--json",
                "comments",
                "--jq",
                ".comments.[] | {body, createdAt}",
            ),
            encoding="UTF-8",
        )

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
        url = sh.stdout(("gh", "pr", "view", branch, "--json", "url"))
        return cls(branch, url, since)

    @classmethod
    def wait_for(cls, branch: str, since: datetime, timeout: int = 60) -> Self:
        def branch_pr() -> Self:
            assert sh.success(("gh", "pr", "view", branch))
            return cls.from_branch(branch, since)

        return wait.for_(branch_pr, timeout=timeout, sleep=5)


def commit_and_push(
    workdir: Path, branch: Branch, message: object = None
) -> None:
    with sh.cd(workdir):
        sh.run(("git", "commit", "-m", message))
        sh.run(("git", "push", "origin", f"{branch}:{branch}"))
