#!/usr/bin/env -S python3.12 -P
from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from typing import Tuple

from lib import ansi
from lib.parse import Parse
from lib.sh import sh
from lib.tf_lock.lib.env import tf_working_dir
from lib.types import Environ
from lib.types import OSPath
from lib.user_error import UserError

from .lib.env import get_current_host
from .lib.env import get_current_user
from .tf_lock_info import cache_get
from .tf_lock_info import tf_lock_info

HERE = sh.get_HERE(__file__)
TF_LOCK_EHELD = 3


@dataclass(frozen=True)
class TFLockUser:
    username: str
    host: str

    pr_number: int | None = None
    repo: str | None = None
    org: str | None = None

    @classmethod
    def from_string(cls, lock_user: str) -> Self:
        p = Parse(lock_user)

        username = p.before.first("@")
        host = p.after.first("@")
        if host.endswith(".github.invalid"):
            repo = host.after.first(".").before.last(".", ".", ".")
            return cls(
                username=username,
                host=host,
                pr_number=int(host.before.first(".")),
                repo=repo,
                org=host.after.first(repo, ".").before.last(".github.invalid"),
            )
        else:
            return cls(username=username, host=host)

    @property
    def pr_url(self) -> str | None:
        if self.pr_number is None:
            return None
        else:
            return f"https://github.com/{self.org}/{self.repo}/pull/{self.pr_number}"

    def eheld_message(self) -> str:
        result = (
            f"User {ansi.TEAL}{self.username}{ansi.RESET} is holding the lock"
        )
        if self.pr_url is not None:
            return (
                result + f" in this PR: {ansi.BLUE}{self.pr_url}{ansi.RESET}"
            )
        else:
            return (
                result
                + f". It looks like they took it manually. (hostname={self.host})"
            )


def info(msg: object) -> None:
    from sys import stderr

    print(msg, file=stderr, flush=True)


def assert_dict_of_strings(json: object) -> dict[str, str]:
    assert isinstance(json, dict), json

    # https://github.com/microsoft/pyright/discussions/6577
    for key, val in json.items():  # pyright: ignore  # unknown types
        assert isinstance(key, str), (key, json)
        assert isinstance(val, str), (val, json)

    from typing import cast

    return cast(dict[str, str], json)


def get_lock_info(root_module: OSPath) -> Tuple[bool, dict[str, str]]:

    result = dict(tf_lock_info(root_module))

    lock = result.pop("lock")
    assert isinstance(lock, bool), lock

    return lock, assert_dict_of_strings(result)


def tf_lock_release(root_module: OSPath, env: Environ) -> None:
    lock, lock_info = get_lock_info(root_module)
    if not lock:
        info(f"tf-lock-release: success: {root_module}")
        return

    tf_user = f"{get_current_user(env)}@{get_current_host(env)}"
    lock_user = lock_info["Who"]
    if tf_user == lock_user:
        with sh.cd(tf_working_dir(root_module)):
            cache = cache_get(root_module)
            if cache:
                try:
                    sh.json(("gcloud", "storage", "rm", cache))
                except sh.ShError:
                    pass  # already unlocked
                tf_log = open("tf-log.hcl", "x")
                tf_log.write("success")
            else:
                sh.run((
                    "terraform",
                    "force-unlock",
                    "-force",
                    "--",
                    lock_info["ID"],
                ))

        info(f"tf-lock-release: success: {root_module}({lock_user})")

    else:
        raise UserError(
            f"""\
tf-lock-release: failure: not {lock_user}: {root_module}({tf_user})
{TFLockUser.from_string(lock_user).eheld_message()}

(hint: to force, set $USER and/or $HOST explicitly)
""",
            code=TF_LOCK_EHELD,
        )


@UserError.handler
def main() -> None:
    from os import environ
    from sys import argv

    args = argv[1:]
    if args:
        paths = [OSPath(arg) for arg in args]
    else:
        paths = [OSPath(".")]

    from os import environ

    with sh.quiet():
        for path in paths:
            tf_lock_release(path, env=environ.copy())


if __name__ == "__main__":
    raise SystemExit(main())
