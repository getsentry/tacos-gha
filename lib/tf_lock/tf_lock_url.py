#!/usr/bin/env python3
"""Print the URL to the terraform state lock for the IAC.

This will require lock-acquire permission if the lock url is not already cached.
No arguments: like terraform/terragrunt this operates on $PWD.
"""

from __future__ import annotations

from lib.sh import sh
from lib.types import ExitCode
from lib.types import OSPath
from lib.user_error import UserError

from .tf_lock_info import cache_get
from .tf_lock_info import tf_lock_info


def tf_lock_url(tg_root_module: OSPath) -> str:
    path = cache_get(tg_root_module)
    if path is not None:
        return path

    # cache miss! go figure out the lock url (slowly)
    with sh.cd(tg_root_module):
        sh.run(("tf-lock-acquire",))
        tf_lock_info(tg_root_module)
        sh.run(("tf-lock-release",))

    path = cache_get(tg_root_module)
    assert isinstance(path, str)
    return path


@UserError.handler
def main() -> ExitCode:
    # with sh.quiet():
    print(tf_lock_url(OSPath.cwd()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
