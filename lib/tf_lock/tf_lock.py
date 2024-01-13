from __future__ import annotations

from typing import Tuple

from lib import json
from lib.sh import sh
from lib.types import Path


def get_lock_info(root_module: Path) -> Tuple[bool, dict[str, str]]:
    result = sh.json(("tf-lock-info", root_module))
    assert isinstance(result, dict)

    lock = result.pop("lock")
    assert isinstance(lock, bool)

    return lock, json.assert_dict_of_strings(result)


def force_unlock(root_module: Path) -> None:
    """Unlock forcefully, regardless of who has the lock."""
    lock, lock_info = get_lock_info(root_module)
    if lock:
        user, host = lock_info["Who"].split("@")
        sh.run(
            (
                "env",
                f"GETSENTRY_SAC_VERB=apply",
                f"USER={user}",
                f"HOST={host}",
                "sudo-gcp",
                "tf-lock-release",
                root_module,
            )
        )
    else:
        sh.debug("already unlocked:", root_module)
