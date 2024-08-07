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
from lib.functions import now as mknow
from lib.sh import sh
from lib.types import Generator

from . import app
from .types import URL
from .types import Branch
from .types import CheckName
from .types import Label
from .types import Message
from .types import WorkflowName
from .up_to_date import up_to_date

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
        branch: Branch,
        message: Message,
        *,
        draft: bool = False,
        **attrs: object,
    ) -> Self:
        sh.run(("git", "checkout", "-b", branch, "--track", "origin/main"))
        since = mknow()
        commit_and_push(branch, message)
        url = sh.stdout(
            ("gh", "pr", "create", "--fill-first", "--head", branch)
            + (("--draft",) if draft else ())
        )
        return cls(branch, url, since, draft, **attrs)

    @contextmanager
    @classmethod
    def opened(cls, branch: Branch, message: Message) -> Generator[Self]:
        pr = cls.open(branch, message)
        sh.banner("PR opened:", pr.url)
        try:
            yield pr
        finally:
            pr.close()

    def close(
        self,
        app_installation: app.Installation | None = None,
        now: datetime | None = None,
    ) -> datetime:
        sh.banner("deleting branch")
        since = mknow()
        try:
            sh.run(
                (
                    "gh",
                    "pr",
                    "close",
                    self.url,
                    "--comment",
                    "automatic test cleanup",
                    "--delete-branch",
                ),
                env=(
                    {"GH_TOKEN": app_installation.token(now=now)}
                    if app_installation is not None
                    else None
                ),
            )
        except CalledProcessError:
            # might already be closed
            if not self.is_closed():
                raise
        return since

    def is_closed(self) -> bool:
        status = sh.stdout(
            ("gh", "pr", "view", self.url, "--json", "state", "--jq", ".state")
        )
        return status in ["CLOSED", "MERGED"]

    def approve(
        self, app_installation: app.Installation, now: datetime | None = None
    ) -> datetime:
        since = mknow()
        sh.run(
            ("gh", "pr", "review", "--approve", self.url),
            env={"GH_TOKEN": app_installation.token(now=now)},
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

    def is_passing_checks(self) -> bool:
        status = sh.stdout((
            "gh",
            "pr",
            "checks",
            self.url,
            "--json",
            "state",
            "--required",
            "--jq",
            'all(.[]; .state == "SUCCESS" or .state == "SKIPPED")',
        ))
        return status == "true"

    def add_label(self, label: Label) -> datetime:
        """Returns a timestamp from *just before* the label was added."""
        sh.banner(f"adding label {label} to PR:")
        since = mknow()
        sh.run(("gh", "pr", "edit", self.url, "--add-label", label))
        return since

    def merge(self) -> datetime:
        sh.banner("merging PR")
        since = mknow()
        sh.run(("gh", "pr", "merge", self.url, "--squash"))
        return since

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
        self,
        workflow: WorkflowName | None = None,
        check_name: CheckName | None = None,
    ) -> CheckFilter:
        from .check import CheckFilter

        return CheckFilter(self, workflow, check_name)

    def toggle_draft(self) -> datetime:
        since = mknow()
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
            if not sh.success(("gh", "pr", "view", branch)):
                return None
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


def commit_and_push(branch: Branch, message: object = None) -> datetime:
    since = mknow()
    sh.run(("git", "commit", "-qam", message))
    with up_to_date():
        sh.run(("git", "show", "--stat"))
        sh.run(("git", "push", "origin", f"HEAD:{branch}"))
    return since
