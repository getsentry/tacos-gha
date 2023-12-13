from __future__ import annotations

from lib.sh import sh


def run(workflow: str) -> None:
    """Trigger a workflow by name."""
    sh.run(("gh", "workflow", "run", workflow))
