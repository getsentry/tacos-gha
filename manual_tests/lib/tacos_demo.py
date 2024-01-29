#!/usr/bin/env py.test
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Self

from lib.constants import NOW
from lib.constants import USER
from lib.parse import Parse
from lib.sh import sh
from lib.types import Generator
from lib.types import OSPath
from manual_tests.lib.gh import gh
from manual_tests.lib.slice import Slice
from manual_tests.lib.slice import Slices

# FIXME: we need a better way to demarcate tf-plan in comments
COMMENT_TAG = '<!-- thollander/actions-comment-pull-request "'
APP_INSTALLATION_REVIEWER = "op://Team Tacos gha dev/gh-app--tacos-gha-reviewer/app-installation/sentryio-org"


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
        gh.commit_and_push(demo, branch, message)
        self = cls.open(demo, branch, slices=slices, draft=draft)

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

    def get_plans(
        self, since: datetime | None = None
    ) -> dict[Slice, gh.Comment]:
        """Map Slices to the text of PR comments containing their tf-plan."""
        if since is None:
            since = self.since

        assert self.check("Terraform Plan").wait(since, timeout=180).success
        plan_tag = COMMENT_TAG + "plan("
        result: dict[Slice, gh.Comment] = {}
        for comment in self.comments(since):
            lastline = Parse(comment).after.last("\n")
            if not lastline.startswith(plan_tag):
                continue

            slice = Slice(Parse(lastline).between(plan_tag, ")"))
            slice = slice.relative_to(self.slices.subpath)

            result[slice] = comment
        return result

    def approve(
        self,
        app_installation: gh.app.Installation | None = None,
        jwt: gh.JWT | None = None,
        now: datetime = NOW,
    ) -> datetime:
        if app_installation is None:
            app_installation = gh.app.Installation.from_1password(
                APP_INSTALLATION_REVIEWER
            )
        if jwt is None:
            jwt = gh.JWT(app_installation.app, app_installation.secret, now)
        return super().approve(app_installation, jwt)


def edit_workflow_versions(
    demo: gh.LocalRepo, tacos_branch: gh.Branch
) -> None:
    sh.banner("updating workflow files")
    workflow_dir = demo.path / ".github/workflows"
    with sh.cd(workflow_dir):
        for workflow in OSPath(".").glob("*.yml"):
            sh.run(
                (
                    "sed",
                    "-ri",
                    "-e",
                    "#".join(
                        (
                            rf"s",
                            rf"(@|refs/heads/)[^[:space:]]+[[:space:]]*$",
                            rf"\1{tacos_branch}",
                            rf"g",
                        )
                    ),
                    workflow,
                )
            )
        sh.run(("git", "add", "-u", "."))
        sh.run(
            (
                "git",
                "commit",
                "-m",
                f"point workflows at branch: {tacos_branch}",
            )
        )


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

    # NB: setting an upstream tracking branch makes `gh pr` stop working well
    sh.run(("git", "checkout", "-B", branch))

    slices.edit()
    return branch, message
