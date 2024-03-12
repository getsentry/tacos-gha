from __future__ import annotations

from typing import Iterable

from lib.sh import sh
from lib.types import Path


def plan_is_clean(tf_root_modules: Iterable[Path]) -> bool:
    """
    Returns whether running terraform plan differs from the current state
    """
    sh.banner("checking tf plan...")
    returncode = sh.returncode(
        ("sudo-gcp", "terragrunt")
        + tuple(
            f"--terragrunt-include-dir={tf_root_module}"
            for tf_root_module in tf_root_modules
        )
        + ("run-all", "plan", "--detailed-exitcode")
    )

    if returncode == 0:
        sh.banner("plan status: clean")
        return True
    elif returncode == 2:
        sh.banner("plan status: dirty")
        return False
    else:
        raise AssertionError(f"unexpected error: exit code {returncode}")


def init(tf_root_modules: Iterable[Path]) -> None:
    sh.run(
        # "state-admin" permission needed to create the initial gcs objects
        ("env", "GETSENTRY_SAC_VERB=state-admin", "sudo-gcp", "terragrunt")
        + tuple(
            f"--terragrunt-include-dir={tf_root_module}"
            for tf_root_module in tf_root_modules
        )
        + ("run-all", "init")
    )


def apply(tf_root_modules: Iterable[Path]) -> None:
    sh.run(
        ("env", "GETSENTRY_SAC_VERB=apply", "sudo-gcp", "terragrunt")
        + tuple(
            f"--terragrunt-include-dir={tf_root_module}"
            for tf_root_module in tf_root_modules
        )
        + ("run-all", "apply", "--auto-approve")
    )
