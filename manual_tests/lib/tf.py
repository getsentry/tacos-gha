from __future__ import annotations

from lib import sh


def plan_clean() -> bool:
    """
    Returns whether running terraform plan differs from the current state
    """
    return sh.success(
        ("sudo-sac", "terragrunt", "run-all", "plan", "--detailed-exitcode")
    )
