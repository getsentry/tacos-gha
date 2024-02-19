"""pytest fixtures specific to tacos-gha demo"""

from __future__ import annotations

from typing import Callable

from pytest import fixture

from lib import json
from lib import wait
from lib.constants import NOW
from lib.constants import TACOS_GHA_HOME
from lib.functions import one
from lib.sh import sh
from lib.sh.cd import cd
from lib.types import Environ
from lib.types import Generator
from lib.types import OSPath
from lib.types import Path
from spec.lib import tacos_demo
from spec.lib import tf
from spec.lib.gh import gh
from spec.lib.slice import Slices

# you forgot to commit if these paths have pending edits
GHA_RELEVANT_PATHS = (
    ".envrc",
    ".github",
    "bin",
    "lib/ci",
    "lib/gcloud",
    "lib/getsentry-sac",
    "lib/github_actions",
    "lib/tacos",
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


# TODO(P3): refactor to an object that takes token in constructor
@fixture
def cli_auth_gcloud(
    home: tuple[OSPath, OSPath], xdg_environ: Environ
) -> Environ:
    # NOTE: must use $HOME here because (ofc) gcloud doesn't respect xdg-config-home
    config_old, config_new = tuple(home / ".config/gcloud" for home in home)
    config_new.parent.mkdir(parents=True, exist_ok=True)
    config_new.symlink_to(config_old)

    # https://fig.io/manual/gcloud/config/config-helper
    gcloud_config = sh.json((
        "tty-attach",
        "gcloud",
        "config",
        "config-helper",
        "--format",
        "json(configuration.properties.core.account,credential.access_token)",
    ))
    gcloud_token = json.deepget(
        gcloud_config, str, "credential", "access_token"
    )

    # for the gcloud CLI
    # https://cloud.google.com/sdk/docs/authorizing#auth-login
    xdg_environ["CLOUDSDK_AUTH_ACCESS_TOKEN"] = gcloud_token

    # for the gcloud terraform provider
    # https://registry.terraform.io/providers/hashicorp/google/latest/docs/guides/provider_reference#access_token
    xdg_environ["GOOGLE_OAUTH_ACCESS_TOKEN"] = gcloud_token

    # this is here mostly to help gcloud generate valid error messages
    # https://stackoverflow.com/a/44824175/146821
    xdg_environ["CLOUDSDK_CORE_ACCOUNT"] = json.deepget(
        gcloud_config, str, "configuration", "properties", "core", "account"
    )
    return xdg_environ


# TODO(P3): refactor to an object that takes token in constructor
@fixture(scope="session")
def cli_auth_gh(session_environ: Environ) -> Environ:
    session_environ["GH_TOKEN"] = sh.stdout(("gh", "auth", "token"))
    return session_environ


@fixture(scope="session")
def cli_auth_op() -> None:
    """Get 1password to ask for touch ASAP, so tests can run without me."""
    tacos_demo.get_reviewer()


@fixture
def git_config(environ: Environ) -> Environ:
    # clear out any overriding environment vars
    for var in environ:
        if var.startswith("GIT_"):
            del environ[var]

    git_config = TACOS_GHA_HOME / "etc/gitconfig"
    environ["GIT_CONFIG_GLOBAL"] = str(git_config)
    return environ


@fixture(scope="session")
def session_environ(
    cli_auth_gh: Environ, cli_auth_op: None
) -> Generator[Environ]:
    """Several small customizations to the default environ, for tacos-demo."""
    yield cli_auth_gh

    # these exist only for pytest fixture dependency hinting
    del cli_auth_op


@fixture
def environ(git_config: Environ) -> Generator[Environ]:
    """Several small customizations to the default environ, for tacos-demo."""
    yield git_config


@fixture
def cwd(cli_auth_gcloud: Environ) -> Generator[OSPath]:
    """Several small customizations to the default cwd, for tacos-demo."""
    yield OSPath(cli_auth_gcloud["PWD"])


@fixture
def demo(cwd: OSPath, git_remote: gh.RemoteRepo) -> Generator[gh.LocalRepo]:
    """A local, cloned working copy of the "demo" repo."""
    with git_remote.cloned(cwd) as clone:
        yield clone


@fixture
def workdir(demo: gh.LocalRepo, environ: Environ) -> Generator[OSPath]:
    sh.banner("loading .envrc settings")
    with cd(TACOS_GHA_HOME, environ):
        # disallow direnv from unloading our test environment:
        for var in environ:
            if var.startswith("DIRENV_"):
                del environ[var]

        with cd(demo.workdir, environ):
            yield demo.workdir


@fixture
def slices_subpath(workdir: OSPath, user: str, test_name: str) -> Path:
    """which subpath of workdir should we search for slices?"""
    # TODO: update actions for minimal slice names
    ###return Path(f"env.{user}")
    subpath = OSPath(f"terraform/env.{user}/{test_name}")
    if not subpath.exists():
        message = f"first-time setup: {subpath}"
        sh.banner(message)
        sh.run(("mkdir", "-p", subpath.parent))
        # note: macos cp has no -r option
        sh.run(("cp", "terraform/env/.gitignore", subpath.parent))
        sh.run(("cp", "-a", "terraform/env/prod", subpath))
        sh.run(("git", "add", subpath.parent))

        all_slices = Slices.from_path(workdir, subpath)
        with sh.cd(all_slices.path):
            # if the slice never existed before,
            # this is needed to create GCS objects
            tf.init(all_slices)
        all_slices.force_unlock()
        all_slices.apply()

        # NOTE: terragrunt apply renders templates, causing some diff
        sh.run(("git", "add", subpath))

        sh.banner("first-time setup: commit and push")
        pr = gh.PR.open(
            f"auto-setup/{user}/{NOW.isoformat().replace(':', '_')}/{test_name}",
            message,
        )

        sh.banner("first-time setup: approve and merge")
        pr.approve(tacos_demo.get_reviewer())
        pr.merge()
        wait.for_(pr.is_closed)

    return subpath


@fixture
def slices_cleanup() -> Callable[[Slices], None]:
    """called before and after selected slices are used in test"""
    return Slices.force_unlock


@fixture
def slices(
    workdir: OSPath,
    slices_subpath: Path,
    slices_cleanup: Callable[[Slices], None],
) -> Generator[Slices]:
    slices_all = Slices.from_path(workdir, slices_subpath)
    slices = slices_all.random()
    slices_cleanup(slices_all)
    yield slices
    slices_cleanup(slices_all)


@fixture
def tacos_branch() -> str:
    with sh.cd(TACOS_GHA_HOME):
        try:
            result = one(
                sh.lines(("git", "symbolic-ref", "-q", "--short", "HEAD"))
            )
        except AssertionError:
            raise AssertionError(
                "Could not find a name for your git branch."
                + " Are you on a detached HEAD?"
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
