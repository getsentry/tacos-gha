#!/usr/bin/env py.test
from __future__ import annotations

import dataclasses
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from functools import cache
from typing import Iterable
from typing import Self

from lib.constants import NOW
from lib.constants import USER
from lib.parse import Parse
from lib.sh import sh
from lib.types import Generator
from lib.types import OSPath
from lib.types import Path
from spec.lib.gh import gh
from spec.lib.slice import Slice
from spec.lib.slice import Slices

COMMENT_TAG = '<!-- getsentry/tacos-gha "'
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
        sh.run(("git", "checkout", "-q", "origin/main"))
        edit_workflow_versions(demo, tacos_branch)
        branch, message = edit_slices(slices, test_name, branch, message)
        self = cls.open(branch, message, slices=slices, draft=draft)

        message = "PR opened:"
        if draft:
            message = "Draft " + message
        sh.banner(message, self.url)

        return self

    def close(
        self,
        app_installation: gh.app.Installation | None = None,
        now: datetime | None = None,
    ) -> datetime:
        return super().close(app_installation, now)

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
        self, since: datetime | None = None, job_filter: str | None = None
    ) -> dict[gh.CheckName, dict[Slice, gh.Comment]]:
        """Map Slices to the text of PR comments containing their tf-plan."""
        if since is None:
            since = self.since

        return parse_comments(
            job_filter, self.slices.subpath, self.comments(since)
        )

    def get_comments_for_job(
        self, job: str, since: datetime | None = None
    ) -> dict[Slice, gh.Comment]:
        comments = self.get_comments_by_job(since, job_filter=job)
        if comments:
            return comments[job]
        else:
            return {}

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

    def with_slices(self, slices: Slices) -> Self:
        return dataclasses.replace(self, slices=slices)

    def __str__(self) -> str:
        return self.url


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

    slices.edit()
    return branch, message


def parse_comments(
    job_filter: str | None,
    slices_subpath: Path,
    comments: Iterable[gh.Comment],
) -> dict[gh.CheckName, dict[Slice, gh.Comment]]:
    result: dict[gh.CheckName, dict[Slice, gh.Comment]] = {}
    for comment in comments:
        for job, slice, comment in parse_comment(
            job_filter, slices_subpath, comment
        ):
            job_comments = result.setdefault(job, {})
            job_comments[slice] = comment
    return result


def parse_comment(
    job_filter: str | None, slices_subpath: Path, comment: str
) -> Generator[tuple[str, Slice, str]]:
    remainder = comment
    while True:
        comment, tag_start, remainder = remainder.partition(COMMENT_TAG)
        if not tag_start:
            return

        tag, tag_end, remainder = remainder.partition(COMMENT_TAG_END)

        tag = Parse(tag)
        job = tag.before.first("(")  # )
        if job_filter is not None and job != job_filter:
            continue  # this is not the job_filter you're looking for

        comment = "".join((comment, tag_start, tag, tag_end))

        parsed = tag.between("(", ")")
        if parsed == tag:
            slice = Slice(".")
        else:
            slice = Slice(parsed)
            slice = slice.relative_to(slices_subpath)
        yield job, slice, comment
