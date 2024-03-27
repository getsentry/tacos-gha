#!/usr/bin/env python3.12
from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from typing import Tuple

from lib import ansi
from lib import json
from lib.parse import Parse
from lib.sh import sh
from lib.types import Environ
from lib.types import OSPath
from lib.types import Path
from lib.user_error import UserError

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


def get_current_user(env: Environ) -> str:
    for var in ("USER", "LOGNAME"):
        if var in env:
            return env[var]
    else:
        import getpass

        return getpass.getuser()


def get_current_host(env: Environ) -> str:
    for var in ("HOST", "HOSTNAME"):
        if var in env:
            return env[var]
    else:
        import socket

        return socket.gethostname()


def assert_dict_of_strings(json: object) -> dict[str, str]:
    assert isinstance(json, dict), json

    # https://github.com/microsoft/pyright/discussions/6577
    for key, val in json.items():  # pyright: ignore  # unknown types
        assert isinstance(key, str), (key, json)
        assert isinstance(val, str), (val, json)

    from typing import cast

    return cast(dict[str, str], json)


def get_lock_info(root_module: Path) -> Tuple[bool, dict[str, str]]:
    try:
        result = sh.json((HERE / "tf-lock-info", str(root_module)))
    except sh.CalledProcessError as error:
        # error message was already printed by subcommand
        raise UserError(code=error.returncode)

    assert isinstance(result, dict), result

    lock = result.pop("lock")
    assert isinstance(lock, bool), lock

    return lock, assert_dict_of_strings(result)


def tf_lock_release(root_module: Path, env: Environ) -> UserError | None:
    lock, lock_info = get_lock_info(root_module)
    if not lock:
        info(f"tf-lock-release: success: {root_module}")
        return None

    tf_user = f"{get_current_user(env)}@{get_current_host(env)}"
    lock_user = lock_info["Who"]
    if tf_user == lock_user:
        try:
            with sh.cd(tf_working_dir(root_module)):
                sh.run(
                    (
                        "terraform",
                        "force-unlock",
                        "-force",
                        "--",
                        lock_info["ID"],
                    )
                )
        except sh.CalledProcessError as error:
            # error message was already printed by subcommand
            return UserError(code=error.returncode)

        info(f"tf-lock-release: success: {root_module}({lock_user})")
        return None

    else:
        return UserError(
            f"""\
tf-lock-release: failure: not {lock_user}: {root_module}({tf_user})
{TFLockUser.from_string(lock_user).eheld_message()}

(hint: to force, set $USER and/or $HOST explicitly)
""",
            code=TF_LOCK_EHELD,
        )


def tf_working_dir(root_module: Path) -> Path:
    """dereference terragrunt indirection, if any"""

    if OSPath(root_module / "terragrunt.hcl").exists():
        with sh.cd(root_module):
            sh.run(("terragrunt", "validate-inputs"))
            info = sh.json(("terragrunt", "terragrunt-info"))
            info = json.assert_dict_of_strings(info)
            return Path(info["WorkingDir"])
    else:
        return root_module


@UserError.handler
def main() -> None:
    from os import environ
    from sys import argv

    args = argv[1:]
    if args:
        paths = [Path(arg) for arg in args]
    else:
        paths = [Path(".")]

    from os import environ

    with sh.quiet():
        successes = 0
        for path in paths:
            if tf_lock_release(path, env=environ.copy()) is None:
                successes += 1
        failures = len(paths) - successes
        sh.info(f"Successfully unlocked {successes} slices.")
        sh.info(f"Failed to unlock {failures} slices.")


if __name__ == "__main__":
    raise SystemExit(main())
