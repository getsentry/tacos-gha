#!/usr/bin/env python3
"""Acquire the terraform state lock and print its ID (an integer)"""

from __future__ import annotations

import asyncio

from lib import ansi
from lib.parse import Parse
from lib.sh import sh
from lib.types import Environ
from lib.types import OSPath
from lib.types import Path

from .lib.acquire import DEBUG
from .lib.acquire import ExitCode
from .lib.acquire import acquire
from .lib.env import HOST
from .lib.env import TF_LOCK_EHELD
from .lib.env import USER
from .lib.env import tf_working_dir


def tf_lock_acquire(root_module: Path, env: Environ) -> ExitCode:
    while True:
        lock_info = sh.json(("tf-lock-info", root_module))
        assert isinstance(lock_info, dict), lock_info
        lock = lock_info["lock"]

        assert isinstance(lock, bool), lock

        if lock:
            lock_user = lock_info["Who"]
            tf_user = f"{USER}@{HOST}"

            if lock_user == tf_user:
                # already done!
                sh.info(f"tf-lock-acquire: success: {lock_user}")
                sh.info(f"{lock_info}")
                return 0
            else:
                sh.info(
                    f"tf-lock-acquire: failure: not {lock_user}: {tf_user}"
                )
                sh.info(
                    f"The terraform/terragrunt slice(s) your PR is touching are locked."
                )
                p = Parse(lock_user)
                username = p.before.first("@")
                # a pr holds the lock.
                if "github" in str(lock_user):
                    pr_number = p.after.first("@").before.first(".")
                    repo_name = p.after.first(".").before.last(".", ".", ".")
                    org_name = p.after.first(repo_name, ".").before.last(
                        ".github"
                    )
                    pr_link = f"https://github.com/{org_name}/{repo_name}/pull/{pr_number}"
                    sh.info(
                        f"User {username} is holding the lock in this PR: {pr_link}"
                    )
                    sh.info((
                        f"{ansi.TEAL}User {username} is holding the lock in this PR: {pr_link}{ansi.RESET}"
                    ))
                else:
                    host = p.after.first("@")
                    sh.info((
                        f"{ansi.TEAL}User {username} is holding the lock. It looks like they took it manually, from {host}.{ansi.RESET}"
                    ))

                sh.info(f"Please talk to the engineer holding the lock!")
                return TF_LOCK_EHELD

        root_module_path = OSPath(root_module)
        assert isinstance(root_module_path, OSPath), root_module_path
        with sh.cd(tf_working_dir(root_module_path)):
            return asyncio.run(acquire(), debug=DEBUG > 0)
        # start over


def main() -> ExitCode:
    from os import environ
    from sys import argv

    args = argv[1:]
    if args:
        paths = [Path(arg) for arg in args]
    else:
        paths = [Path(".")]

    from os import environ

    for path in paths:
        if ret_code := tf_lock_acquire(path, env=environ.copy()):
            return ret_code

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
