#!/usr/bin/env py.test
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from functools import cache
from typing import Self

from lib.constants import NOW
from lib.constants import USER
from lib.functions import one
from lib.parse import Parse
from lib.sh import sh
from lib.types import Generator
from lib.types import OSPath
from spec.lib.gh import gh
from spec.lib.slice import Slice
from spec.lib.slice import Slices

# FIXME: we need a better way to demarcate tf-plan in comments
COMMENT_TAG = '<!-- thollander/actions-comment-pull-request "'
COMMENT_TAG_END = '" -->'
APP_INSTALLATION_REVIEWER = (
    "op://Team Tacos gha"
    " dev/gh-app--tacos-gha-reviewer/app-installation/sentryio-org"
)


@cache
def get_reviewer() -> gh.app.Installation:
    return gh.app.Installation.from_1password(APP_INSTALLATION_REVIEWER)


@dataclass(frozen=True)
class PR(gh.PR):
    slices: Slices

    @classmethod
    def from_pr(cls, pr: gh.PR, slices: Slices) -> Self:
        return cls(**vars(pr), slices=slices)

    @classmethod
    def for_slices(
        cls,
        slices: Slices,
        test_name: str,
        demo: gh.LocalRepo,
        tacos_branch: gh.Branch,
        branch: object = None,
        message: object = None,
        draft: bool = False,
    ) -> Self:
        edit_workflow_versions(demo, tacos_branch)
        branch, message = edit_slices(slices, test_name, branch, message)
        self = cls.open(branch, message, slices=slices, draft=draft)

        sh.banner("PR opened:", self.url)

        return self

    def close(self) -> None:
        super().close()

    @classmethod
    @contextmanager
    def opened_for_slices(
        cls,
        slices: Slices,
        test_name: str,
        demo: gh.LocalRepo,
        tacos_branch: gh.Branch,
        branch: gh.Branch = None,
        message: gh.Message = None,
        draft: bool = False,
    ) -> Generator[Self]:
        with sh.cd(slices.path):
            pr = cls.for_slices(
                slices, test_name, demo, tacos_branch, branch, message, draft
            )
            try:
                yield pr
            finally:
                pr.close()

    def get_comments_by_job(
        self, since: datetime | None = None, job: str | None = None
    ) -> dict[gh.CheckName, dict[Slice, gh.Comment]]:
        """Map Slices to the text of PR comments containing their tf-plan."""
        if since is None:
            since = self.since

        comments: dict[gh.CheckName, dict[Slice, gh.Comment]] = {}
        for comment in self.comments(since):
            lastline = Parse(comment).after.last("\n")
            if not lastline.startswith(COMMENT_TAG):
                continue

            tag = Parse(lastline).after.between(COMMENT_TAG, COMMENT_TAG_END)
            job2 = tag.before.first("(")  # )
            if job is not None and job2 != job:
                continue

            job_comments = comments.setdefault(job2, {})

            slice = Slice(tag.between("(", ")"))
            slice = slice.relative_to(self.slices.subpath)

            job_comments[slice] = comment
        return comments

    def get_comments_for_job(
        self, job: str, since: datetime | None = None
    ) -> dict[Slice, gh.Comment]:
        comments = self.get_comments_by_job(since, job)
        assert one(comments) == job
        return comments[job]

    def get_plans(
        self, since: datetime | None = None
    ) -> dict[Slice, gh.Comment]:
        """Map Slices to the text of PR comments containing their tf-plan."""
        assert self.check("Terraform Plan").wait(since).success
        return self.get_comments_for_job("plan")

    def approve(
        self,
        app_installation: gh.app.Installation | None = None,
        now: datetime | None = None,
    ) -> datetime:
        if app_installation is None:
            app_installation = get_reviewer()
        return super().approve(app_installation, now)


def edit_workflow_versions(
    demo: gh.LocalRepo, tacos_branch: gh.Branch
) -> None:
    sh.banner("updating workflow files")
    workflow_dir = demo.path / ".github/workflows"
    with sh.cd(workflow_dir):
        for workflow in OSPath(".").glob("*.yml"):
            sh.run((
                "sed",
                "-ri",
                "-e",
                "#".join((
                    rf"s",
                    rf"(@|refs/heads/)[^[:space:]]+[[:space:]]*$",
                    rf"\1{tacos_branch}",
                    rf"g",
                )),
                workflow,
            ))
            sh.run(("git", "add", "-u", workflow_dir))


def edit_slices(
    slices: Slices,
    test_name: str,
    branch: gh.Branch = None,
    message: gh.Message = None,
) -> tuple[gh.Branch, gh.Message]:
    sh.banner(f"editing slices")
    for slice in sorted(slices):
        sh.info(f"  * {slice}")
    if branch:
        branch = f"/{branch}"
    else:
        branch = ""

    branch = (
        f"test/{USER}/{NOW.isoformat().replace(':', '_')}/{test_name}{branch}"
    )

    if message:
        message = f" - {message}"
    else:
        message = ""
    message = f"test: {test_name} ({NOW}){message}"

    sh.run(("git", "checkout", "-B", branch))

    slices.edit()
    return branch, message
