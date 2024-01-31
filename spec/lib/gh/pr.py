from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from subprocess import CalledProcessError
from typing import TYPE_CHECKING
from typing import Self
from typing import Sequence

from lib import json
from lib import wait
from lib.functions import now
from lib.sh import sh
from lib.types import Generator
from spec.lib.gh import gh
from spec.lib.xfail import XFailed

from . import app
from .jwt import JWT
from .repo import LocalRepo
from .types import URL
from .types import Branch
from .types import CheckName
from .types import Label
from .types import WorkflowName

APP_INSTALLATION_REVIEWER = (
    "op://Team Tacos gha dev/tacos-gha-reviewer/installation.json"
)


Comment = str  # a PR comment

if TYPE_CHECKING:
    from .check import CheckFilter
    from .check_run import CheckRun

# mypy doesn't understand ParamSpec :(
# pr.py:203: error: Argument 1 to "for_" has incompatible type "Callable[[], Self | None]"; expected "Callable[[], Self | None]"
# mypy: disable-error-code="arg-type"


@dataclass(frozen=True)
class PR:
    branch: Branch
    url: URL
    since: datetime
    draft: bool

    @classmethod
    def open(
        cls,
        repo: LocalRepo,
        branch: Branch,
        *,
        draft: bool = False,
        **attrs: object,
    ) -> Self:
        since = now()
        with sh.cd(repo.path):
            url = sh.stdout(
                ("gh", "pr", "create", "--fill-first", "--head", branch)
                + (("--draft",) if draft else ())
            )
        return cls(branch, url, since, draft, **attrs)

    @contextmanager
    @classmethod
    def opened(cls, repo: LocalRepo, branch: Branch) -> Generator[Self]:
        pr = cls.open(repo, branch)
        sh.banner("PR opened:", pr.url)
        try:
            yield pr
        finally:
            pr.close()

    def close(self) -> None:
        sh.banner("deleting branch")
        try:
            sh.run((
                "gh",
                "pr",
                "close",
                self.url,
                "--comment",
                "automatic test cleanup",
                "--delete-branch",
            ))
        except CalledProcessError:
            # might already be closed
            if not self.is_closed():
                raise

    def is_closed(self) -> bool:
        status = sh.stdout(
            ("gh", "pr", "view", self.url, "--json", "state", "--jq", ".state")
        )
        return status in ["CLOSED", "MERGED"]

    def approve(
        self, app_installation: app.Installation, jwt: JWT
    ) -> datetime:
        since = now()
        sh.run(
            ("gh", "pr", "review", "--approve", self.url),
            env={"GH_TOKEN": app_installation.token(jwt)},
        )
        return since

    def is_approved(self) -> bool:
        status = sh.stdout((
            "gh",
            "pr",
            "view",
            self.url,
            "--json",
            "reviewDecision",
            "--jq",
            ".reviewDecision",
        ))
        return status == "APPROVED"

    def add_label(self, label: Label) -> datetime:
        """Returns a timestamp from *just before* the label was added."""
        sh.banner(f"adding label {label} to PR:")
        since = now()
        sh.run(("gh", "pr", "edit", self.url, "--add-label", label))
        return since

    def merge(self) -> str:
        sh.banner("merging PR")
        try:
            return sh.stdout(("gh", "pr", "merge", self.url, "--squash"))
        except sh.CalledProcessError:
            # + $ gh pr merge --squash https://github.com/getsentry/tacos-gha.demo/pull/363
            # X Pull request #363 is not mergeable: the base branch policy prohibits the merge.
            # To have the pull request merged after all the requirements have been met, add the `--auto` flag.
            # To use administrator privileges to immediately merge the pull request, add the `--admin` flag.
            raise XFailed("terraform changes not yet mergeable")

    def labels(self) -> Sequence[Label]:
        result: list[Label] = []
        for label in sh.lines((
            "gh",
            "pr",
            "view",
            self.url,
            "--json",
            "labels",
            "--jq",
            ".labels.[] | .name",
        )):
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

    def check(
        self, workflow: WorkflowName, check_name: CheckName | None = None
    ) -> CheckFilter:
        from .check import CheckFilter

        return CheckFilter(self, workflow, check_name)

    def toggle_draft(self) -> datetime:
        since = now()
        if self.draft:
            sh.run(("gh", "pr", "ready", self.url))
        else:
            sh.run(("gh", "pr", "ready", "--undo", self.url))
        return since

    @classmethod
    def from_branch(cls, branch: Branch, since: datetime) -> Self:
        url = sh.stdout(("gh", "pr", "view", branch, "--json", "url"))
        draft = sh.json((
            "gh",
            "pr",
            "view",
            branch,
            "--json",
            "isDraft",
            "--jq",
            ".isDraft",
        ))
        assert isinstance(draft, bool)
        return cls(branch, url, since, draft)

    @classmethod
    def wait_for(cls, branch: str, since: datetime, timeout: int = 60) -> Self:
        def branch_pr() -> Self | None:
            assert sh.success(("gh", "pr", "view", branch))
            return cls.from_branch(branch, since)

        return wait.for_(branch_pr, timeout=timeout, sleep=5)

    def get_check_runs(
        self, since: datetime | None = None
    ) -> Generator[CheckRun]:
        """Return the all runs of this check."""
        from . import check_run

        if since is None:
            since = self.since

        for obj in check_run.get_runs_json(self.url):
            run = check_run.CheckRun.from_json(obj)
            if run.started_at > since:
                yield run


def commit_and_push(
    repo: LocalRepo, branch: Branch, message: object = None
) -> None:
    with sh.cd(repo.path):
        sh.run(("git", "commit", "-am", message))
        with gh.up_to_date():
            sh.run(("git", "show", "--stat"))
            sh.run(("git", "push", "origin", f"{branch}:{branch}"))
