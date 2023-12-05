from __future__ import annotations

import contextlib
import os
from os import getenv
from typing import TYPE_CHECKING
from typing import Dict
from typing import Iterable
from typing import Iterator
from typing import List
from typing import MutableMapping
from typing import Union

US_ASCII = "US-ASCII"  # the least-ambiguous encoding
JSONPrimitive = Union[str, int, float, bool, None]
JSONObject = Dict[str, JSONPrimitive]
JSONArray = List[JSONPrimitive]
JSONValue = Union[JSONPrimitive, JSONArray, JSONObject]

if TYPE_CHECKING:
    # strict encapsulation: limit run-time access to just one function each
    from subprocess import CalledProcessError
    from subprocess import CompletedProcess
    from subprocess import Popen

# TODO: centralize reused type aliases
Command = tuple[str, ...]
Yields = Iterator

debug: bool = bool(getenv("DEBUG", "1"))
PS4 = "+ \033[36;1m$\033[m"


def info(msg: tuple[object, ...]) -> None:
    from sys import stderr

    print(*msg, file=stderr, flush=True)


def banner(*msg: str) -> None:
    info(("\033[92;1m", "=" * 8) + msg + ("=" * 8, "\033[m"))


def xtrace(cmd: Command) -> None:
    if debug:
        info((PS4, quote(cmd)))


def cd(
    dirname: str,
    env: MutableMapping[str, str] = os.environ,
    direnv: bool = True,
) -> None:
    from os import chdir

    xtrace(("cd", dirname))
    chdir(dirname)
    if direnv:
        direnv_json: JSONValue = json(("direnv", "export", "json"))
        if not isinstance(direnv_json, dict):
            raise TypeError(f"expected dict, got {type(direnv_json)}")
        for key, value in direnv_json.items():
            if value is None:
                env.pop(key, None)
            else:
                assert isinstance(value, str), value
                env[key] = value


def quote(cmd: Command) -> str:
    import shlex

    return " ".join(shlex.quote(arg) for arg in cmd)


def stdout(cmd: Command) -> str:
    return _wait(_popen(cmd, capture_output=True)).stdout.rstrip("\n")


def json(cmd: Command) -> JSONValue:
    """Parse the (singular) json on a subprocess' stdout."""
    import json

    result: JSONValue = json.loads(stdout(cmd))
    return result


def jq(cmd: Command, encoding: str = US_ASCII) -> Iterable[object]:
    """Yield the objects from newline-delimited json on a subprocess' stdout."""
    import json

    process = _popen(cmd, encoding=encoding, capture_output=True)
    assert process.stdout, process.stdout
    for line in process.stdout:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        try:
            result: object = json.loads(line)
        except Exception as error:
            raise error from ValueError(f"bad JSON:\n    {line}")
        else:
            yield result


def success(cmd: Command, returncode: int = 0) -> bool:
    # any non-ascii bytes are ambiguous, here:
    result = _wait(_popen(cmd), check=False)
    return result.returncode == returncode


def _popen(
    cmd: Command, capture_output: bool = False, encoding: str = US_ASCII
) -> Popen[str]:
    import subprocess

    xtrace(cmd)
    if cmd[0] == ":":
        # : is the POSIX-specified shell builtin for 'true', but we've no shell
        cmd = ("true",) + cmd[1:]

    if capture_output:
        stdout = subprocess.PIPE
    else:
        stdout = None

    return subprocess.Popen(cmd, text=True, encoding=encoding, stdout=stdout)


def _wait(
    process: Popen[str],
    input: str | None = None,
    timeout: int | None = None,
    check: bool = True,
) -> CompletedProcess[str]:
    """Stolen from the last half of stdlib subprocess.run; finish a process."""
    with process:
        try:
            stdout, stderr = process.communicate(input, timeout=timeout)
        except:  # Including KeyboardInterrupt, communicate handled that.
            process.kill()
            # We don't call process.wait() as .__exit__ does that for us.
            raise
        retcode = process.poll()
        if check and retcode:
            raise CalledProcessError(
                retcode, process.args, output=stdout, stderr=stderr
            )
    assert retcode is not None, retcode
    from subprocess import CompletedProcess

    return CompletedProcess(process.args, retcode, stdout, stderr)


def run(cmd: Command) -> None:
    _wait(_popen(cmd))


@contextlib.contextmanager
def quiet() -> Yields[bool]:
    global debug
    orig, debug = debug, False
    yield orig
    debug = orig
