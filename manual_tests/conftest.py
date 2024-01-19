"""pytest fixtures specific to tacos-gha demo"""
from __future__ import annotations

from pytest import fixture

from lib import json
from lib.constants import TACOS_GHA_HOME
from lib.functions import one
from lib.sh import sh
from lib.sh.cd import cd
from lib.types import Environ
from lib.types import Generator
from lib.types import OSPath
from lib.types import Path
from manual_tests.lib import tacos_demo
from manual_tests.lib import tf
from manual_tests.lib.gh import gh
from manual_tests.lib.slice import Slices

# you forgot to commit if these paths have pending edits
GHA_RELEVANT_PATHS = (
    ".envrc",
    ".github",
    "bin",
    "lib/ci",
    "lib/gcloud",
    "lib/getsentry-sac",
    "lib/github",
    "lib/tacos",
    "lib/terragrunt",
    "lib/tf_lock",
    "lib/unix",
)


@fixture
def git_remote() -> gh.RemoteRepo:
    """The remote specification of the "demo" repo, on github."""
    return gh.RemoteRepo(
        url="git@github.com:getsentry/tacos-gha.demo",
        # TODO: update actions for minimal slice names
        ###subpath=Path("terraform")
    )


@fixture
def demo(cwd: OSPath, git_remote: gh.RemoteRepo) -> Generator[gh.LocalRepo]:
    """A local, cloned working copy of the "demo" repo."""
    with git_remote.cloned(cwd) as clone:
        yield clone


@fixture
def workdir(demo: gh.LocalRepo, environ: Environ) -> Generator[OSPath]:
    with cd(TACOS_GHA_HOME, environ):
        # disallow direnv from unloading our test environment:
        for var in environ:
            if var.startswith("DIRENV_"):
                del environ[var]

        with cd(demo.workdir, environ):
            yield demo.workdir


@fixture
def slices_subpath(user: str) -> Path:
    """which subpath of workdir should we search for slices?"""
    # TODO: update actions for minimal slice names
    ###return Path(f"env.{user}")
    return Path(f"terraform/env.{user}")


@fixture
def slices(workdir: OSPath, slices_subpath: Path) -> Slices:
    slices = Slices.from_path(workdir, slices_subpath)
    return slices.random()


@fixture
def tacos_branch() -> str:
    with sh.cd(TACOS_GHA_HOME):
        result = one(
            sh.lines(("git", "symbolic-ref", "-q", "--short", "HEAD"))
        )
        # push any GHA-relevant changes
        if result != "main":
            if not sh.success(
                ("git", "diff", "--quiet", "HEAD") + GHA_RELEVANT_PATHS
            ):
                # TODO: amend if the previous commit was a similar auto-commit
                sh.run(
                    (
                        "git",
                        "commit",
                        "--message=auto-commit: GHA deps, for test",
                    )
                    + GHA_RELEVANT_PATHS
                )
                sh.run(("git", "show", "--stat"))

            # either way, ensure that what we committed will be used
            sh.run(
                ("git", "push", "--force-with-lease", "--force-if-includes")
            )
    return result


@fixture
def pr(
    slices: Slices, test_name: str, demo: gh.LocalRepo, tacos_branch: str
) -> Generator[tacos_demo.PR]:
    with tacos_demo.PR.opened_for_slices(
        slices, test_name, demo, tacos_branch
    ) as pr:
        yield pr


GCLOUD_CONFIG = Path(".config/gcloud/configurations")


# TODO: refactor to an object that takes token in constructor, remove autouse
@fixture(autouse=True, scope="session")
def cli_auth_gcloud() -> None:
    from os import environ

    # https://fig.io/manual/gcloud/config/config-helper
    gcloud_config = sh.json(
        (
            "gcloud",
            "config",
            "config-helper",
            "--format",
            "json(configuration.properties.core.account,credential.access_token)",
        )
    )
    gcloud_token = json.deepget(
        gcloud_config, str, "credential", "access_token"
    )

    # for the gcloud CLI
    # https://cloud.google.com/sdk/docs/authorizing#auth-login
    environ["CLOUDSDK_AUTH_ACCESS_TOKEN"] = gcloud_token

    # for the gcloud terraform provider
    # https://registry.terraform.io/providers/hashicorp/google/latest/docs/guides/provider_reference#access_token
    environ["GOOGLE_OAUTH_ACCESS_TOKEN"] = gcloud_token

    # this is here mostly to help gcloud generate valid error messages
    # https://stackoverflow.com/a/44824175/146821
    environ["CLOUDSDK_CORE_ACCOUNT"] = json.deepget(
        gcloud_config, str, "configuration", "properties", "core", "account"
    )


# TODO: refactor to an object that takes token in constructor, remove autouse
@fixture(autouse=True, scope="session")
def cli_auth_gh() -> None:
    from os import environ

    environ["GITHUB_TOKEN"] = sh.stdout(("gh", "auth", "token"))


@fixture
def clean_slices(slices: Slices) -> Generator[Slices]:
    """Ensure that all (relevant) slices are terraform clean."""
    tf.apply(slices.path)

    try:
        yield slices
    finally:
        # cleanup: apply main in case the test left things in a dirty state
        sh.banner("Cleanup: roll back the infrastructure changes")
        sh.run(("git", "-C", slices.path, "reset", "--hard", "origin/main"))
        tf.apply(slices.path)
