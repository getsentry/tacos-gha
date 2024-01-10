from __future__ import annotations

from lib.sh import sh
from lib.types import OSPath


def _plan_exitcode(workdir: OSPath) -> int:
    sh.banner("checking tf plan...")
    with sh.cd(workdir):
        result = sh.returncode(
            (
                "sudo-sac",
                "terragrunt",
                "run-all",
                "plan",
                "--detailed-exitcode",
            )
        )

    if result == 0:
        sh.banner("plan status: clean")
    elif result == 2:
        sh.banner("plan status: dirty")
    else:
        raise AssertionError(f"unexpected error: exit code {result}")

    return result


def plan_clean(workdir: OSPath) -> bool:
    """
    Returns whether running terraform plan differs from the current state
    """
    return _plan_exitcode(workdir) == 0


def plan_dirty(workdir: OSPath) -> bool:
    """
    Returns whether running terraform plan differs from the current state
    """
    return _plan_exitcode(workdir) == 2


def apply(workdir: OSPath) -> None:
    with sh.cd(workdir):
        sh.run(
            (
                "sudo-sac",
                "terragrunt",
                "run-all",
                "apply",
                "--auto-approve",
                "--terragrunt-non-interactive",
            )
        )
