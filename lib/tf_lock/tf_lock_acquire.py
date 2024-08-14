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
            # a pr holds the lock.
            if (
                tf_lock_user.org
                and tf_lock_user.repo
                and tf_lock_user.pr_number
            ):
                if is_pr_closed(
                    tf_lock_user.org, tf_lock_user.repo, tf_lock_user.pr_number
                ):
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


def is_pr_closed(org_name: str, repo_name: str, pr_number: int) -> bool:
    import json
    import os
    from urllib.error import HTTPError
    from urllib.request import Request
    from urllib.request import urlopen

    access_token = os.getenv("GH_TOKEN")
    api_url = f"https://api.github.com/repos/{org_name}/{repo_name}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    req = Request(api_url, headers=headers)

    try:
        with urlopen(req) as response:
            pr_data = json.loads(response.read().decode())
            if pr_data["state"] == "closed":
                return True
    except HTTPError as e:
        if e.code == 404:
            raise ValueError(
                "PR not found or you do not have access to this repository."
            )
        else:
            raise Exception(f"Failed to fetch PR details: {e.code}")

    return False


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
