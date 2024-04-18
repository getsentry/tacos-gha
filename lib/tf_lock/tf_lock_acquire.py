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

            sh.info(
                f"tf-lock-acquire: failure: not {lock_user}: {root_module}({tf_user})"
            )

            lock_user = TFLockUser.from_string(lock_user)
            sh.info(lock_user.eheld_message())

            return TF_LOCK_EHELD

        root_module_path = OSPath(root_module)
        assert isinstance(root_module_path, OSPath), root_module_path
        with sh.cd(tf_working_dir(root_module_path)):
            returncode = asyncio.run(acquire(), debug=DEBUG > 0)
            if returncode != 0:
                return returncode

        # start over


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
