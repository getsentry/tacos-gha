#!/usr/bin/env python3.12
from __future__ import annotations

from typing import Mapping
from typing import Tuple

from lib import json
from lib.sh import sh
from lib.types import OSPath
from lib.types import Path
from lib.user_error import UserError

HERE = sh.get_HERE(__file__)
Environ = Mapping[str, str]
TF_LOCK_EHELD = 3


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


def tf_lock_release(root_module: Path, env: Environ) -> None:
    lock, lock_info = get_lock_info(root_module)
    if not lock:
        info(f"tf-lock-release: success: {root_module}")
        return

    tf_user = f"{get_current_user(env)}@{get_current_host(env)}"
    lock_user = lock_info["Who"]
    if tf_user == lock_user:
        try:
            with sh.cd(tf_working_dir(root_module)):
                sh.run((
                    "terraform",
                    "force-unlock",
                    "-force",
                    "--",
                    lock_info["ID"],
                ))
        except sh.CalledProcessError as error:
            # error message was already printed by subcommand
            raise UserError(code=error.returncode)

        info(f"tf-lock-release: success: {root_module}({lock_user})")

    else:
        raise UserError(
            f"""\
tf-lock-release: failure: not {lock_user}: {root_module}({tf_user})
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

    for path in paths:
        tf_lock_release(path, env=environ.copy())


if __name__ == "__main__":
    raise SystemExit(main())
