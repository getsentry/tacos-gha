"""pytest fixtures specific to tacos-gha demo"""
from __future__ import annotations

from pathlib import Path

from pytest import fixture

from lib import json
from lib.sh import sh
from lib.sh.cd import cd
from lib.types import Generator
from manual_tests.lib import tacos_demo
from manual_tests.lib.gh import gh
from manual_tests.lib.slice import Slices


@fixture
def git_remote(user: str) -> gh.repo.Remote:
    return gh.repo.Remote(
        url="git@github.com:getsentry/tacos-demo",
        subpath=Path(f"terraform/env.{user}/prod/"),
    )


@fixture
def git_clone(
    cwd: Path, git_remote: gh.repo.Remote
) -> Generator[gh.repo.Local]:
    with git_remote.cloned(cwd) as clone:
        yield clone


@fixture
def workdir(git_clone: gh.repo.Local) -> Generator[Path]:
    with cd(git_clone.workdir):
        yield git_clone.workdir


@fixture
def slices(workdir: Path) -> Slices:
    slices = Slices.from_path(workdir)
    return slices.random()


@fixture
def pr(slices: Slices, test_name: str) -> Generator[tacos_demo.PR]:
    with tacos_demo.PR.opened_for_slices(slices, test_name) as pr:
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

    environ["GH_TOKEN"] = sh.stdout(("gh", "auth", "token"))
