#!/usr/bin/env -S python3.12 -P
"""Acquire the terraform state lock and print its ID (an integer)"""

from __future__ import annotations

import asyncio

from lib.sh import sh
from lib.types import ExitCode
from lib.types import OSPath
from lib.types import Path

from .lib.acquire import DEBUG
from .lib.acquire import acquire
from .lib.env import HOST
from .lib.env import TF_LOCK_EHELD
from .lib.env import USER
from .lib.env import tf_working_dir
from .release import TFLockUser
from .tf_lock import force_unlock


def tf_lock_acquire(root_module: Path) -> ExitCode:
    while True:
        try:
            lock_info = sh.json(("tf-lock-info", root_module))
        except sh.CalledProcessError as exc:
            return exc.returncode

        assert isinstance(lock_info, dict), lock_info
        lock = lock_info["lock"]

        assert isinstance(lock, bool), lock

        if lock:
            tf_user = f"{USER}@{HOST}"
            lock_user = lock_info["Who"]
            assert isinstance(lock_user, str)

            if lock_user == tf_user:
                # already done!
                sh.info(
                    f"tf-lock-acquire: success: {root_module}({lock_user})"
                )
                return 0

            tf_lock_user = TFLockUser.from_string(lock_user)
            if tf_lock_user.pr_url:  # a pr holds the lock.
                if is_pr_unlockable(tf_lock_user.pr_url):
                    sh.info("forcing unlock on a closed PR.")
                    force_unlock(root_module)
                    continue

            sh.info(
                f"tf-lock-acquire: failure: not {lock_user}: {root_module}({tf_user})"
            )

            sh.info(tf_lock_user.eheld_message())

            return TF_LOCK_EHELD

        root_module_path = OSPath(root_module)
        assert isinstance(root_module_path, OSPath), root_module_path
        with sh.cd(tf_working_dir(root_module_path)):
            returncode = asyncio.run(acquire(), debug=DEBUG > 0)
            if returncode != 0:
                return returncode

        # start over


# TODO: deduplicate wrt spec.gh.pr.PR.is_closed
def is_pr_unlockable(gh_url: str) -> bool:
    status = sh.stdout(
        ("gh", "pr", "view", gh_url, "--json", "state", "--jq", ".state")
    )
    is_draft = sh.json(
        ("gh", "pr", "view", gh_url, "--json", "isDraft", "--jq", ".isDraft")
    )
    assert isinstance(is_draft, bool)

    return status in ("CLOSED", "MERGED") or is_draft


def main() -> ExitCode:
    from sys import argv

    args = argv[1:]
    if args:
        paths = [Path(arg) for arg in args]
    else:
        paths = [Path(".")]

    with sh.quiet():
        for path in paths:
            if ret_code := tf_lock_acquire(path):
                return ret_code

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
