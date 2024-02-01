from __future__ import annotations

from datetime import datetime

from lib.functions import now
from lib.sh import sh


def run(workflow: str) -> datetime:
    """Trigger a workflow by name. Return a timestamp from *just before*."""
    since = now()
    sh.run(("gh", "workflow", "run", workflow))
    return since
