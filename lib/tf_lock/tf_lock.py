from __future__ import annotations

from typing import Tuple

from lib import json
from lib.sh import sh
from lib.types import Path


def get_lock_info(root_module: Path) -> Tuple[bool, dict[str, str]]:
    lock_info = sh.json(("tf-lock-info", root_module))
    assert isinstance(lock_info, dict)

    lock = lock_info.pop("lock")
    assert isinstance(lock, bool)

    # TODO: sh.show_json(): use jq to highlight
    from json import dumps

    if lock:
        sh.debug(dumps(lock_info, indent=2))

    return lock, json.assert_dict_of_strings(lock_info)


def force_unlock(root_module: Path) -> None:
    """Unlock forcefully, regardless of who has the lock."""
    lock, lock_info = get_lock_info(root_module)
    if lock:
        user, host = lock_info["Who"].split("@")
        sh.run((
            "env",
            f"GETSENTRY_SAC_VERB=apply",
            f"USER={user}",
            f"HOST={host}",
            "sudo-gcp",
            "tf-lock-release",
            root_module,
        ))
