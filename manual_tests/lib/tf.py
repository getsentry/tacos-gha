from __future__ import annotations

from pathlib import Path

from lib.sh import sh


def plan_clean() -> bool:
    """
    Returns whether running terraform plan differs from the current state
    """
    return sh.success(
        ("sudo-sac", "terragrunt", "run-all", "plan", "--detailed-exitcode")
    )


def apply(workdir: Path) -> None:
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
