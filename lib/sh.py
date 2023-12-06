#!/usr/bin/env py.test
from __future__ import annotations

import contextlib
from os import environ
from os import getenv
from subprocess import CalledProcessError as CalledProcessError
from subprocess import TimeoutExpired as TimeoutExpired
from typing import TYPE_CHECKING
from typing import Iterable
from typing import Iterator
from typing import MutableMapping

US_ASCII = "US-ASCII"  # the least-ambiguous encoding
JSONPrimitive = str | int | float | bool | None
JSONObject = dict[str, JSONPrimitive]
JSONArray = list[JSONPrimitive]
JSONValue = JSONPrimitive | JSONArray | JSONObject


if TYPE_CHECKING:
    # strict encapsulation: limit run-time access to just one function each
    from subprocess import CompletedProcess
    from subprocess import Popen

# TODO: centralize reused type aliases
Command = tuple[object, ...]
Yields = Iterator

debug: bool = bool(getenv("DEBUG", "1"))
ANSI_CSI = "\033["
ANSI_RESET = f"{ANSI_CSI}m"
ANSI_GREEN = f"{ANSI_CSI}92;1m"
ANSI_TEAL = f"{ANSI_CSI}36;1m"
PS4 = f"+ {ANSI_TEAL}${ANSI_RESET} "


def info(*msg: object) -> None:
    """Show the user a message."""

    from sys import stderr

    print(*msg, file=stderr, flush=True)


def banner(*msg: object) -> None:
    """Show a colorized, high-visibility message."""
    info(ANSI_GREEN, "=" * 8, *msg, "=" * 8, ANSI_RESET)


def xtrace(cmd: Command) -> None:
    """Simulate bash's xtrace: show a command with copy-pasteable escaping.

    Output is suppressed when `sh.debug` is False.
    """
    if debug:
        info("".join((PS4, quote(cmd))))


def cd(
    dirname: str, direnv: bool = True, env: MutableMapping[str, str] = environ
) -> None:
    from os import chdir

    xtrace(("cd", dirname))
    chdir(dirname)
    # TODO: set env[PWD] to absolute path
    if direnv:
        run(("direnv", "allow"))
        direnv_json: JSONValue = json(("direnv", "export", "json"))
        if not isinstance(direnv_json, dict):
            raise AssertionError(f"expected dict, got {type(direnv_json)}")
        for key, value in direnv_json.items():
            if value is None:
                env.pop(key, None)
            else:
                assert isinstance(value, str), value
                env[key] = value


def quote(cmd: Command) -> str:
    """Escape a command to copy-pasteable shell form.

    >>> print(quote(("ls", "1 2", 3, "4")))
    ls '1 2' 3 4
    """
    import shlex

    return " ".join(shlex.quote(str(arg)) for arg in cmd)


def stdout(cmd: Command) -> str:
    r"""Get the output of a command.

    Trailing newlines are stripped for convenience.

    >>> stdout(("echo", "ok"))
    'ok'
    """
    return _wait(_popen(cmd, capture_output=True)).stdout.rstrip("\n")


def json(cmd: Command) -> JSONValue:
    """Parse the (singular) json on a subprocess' stdout.

    >>> json(("echo", '{"a": "b", "c": 3}'))
    {'a': 'b', 'c': 3}
    """
    import json

    result: JSONValue = json.loads(stdout(cmd))
    return result


def jq(cmd: Command, encoding: str = US_ASCII) -> Iterable[object]:
    """Yield each object from newline-delimited json on a subprocess' stdout.

    >>> tuple(jq(("seq", 3)))
    (1, 2, 3)
    """
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
            raise ValueError(f"bad JSON:\n    {line}") from error
        else:
            yield result


def success(cmd: Command, returncode: int = 0) -> bool:
    """Run a command and report whether it was successful.

    >>> success(('true',))
    True
    >>> success(('false',))
    False

    Optionally, specify an expected return code:

    >>> success(('false',), returncode=1)
    True
    """
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

    return subprocess.Popen(
        tuple(str(arg) for arg in cmd),
        text=True,
        encoding=encoding,
        stdout=stdout,
    )


def _wait(
    process: Popen[str],
    input: str | None = None,
    timeout: float | None = None,
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
    """Run a command to completion. Raises on error.

    >>> run(('echo', 'ok'))
    >>> run(('false', 'not ok'))
    Traceback (most recent call last):
        ...
    subprocess.CalledProcessError: Command '('false', 'not ok')' returned non-zero exit status 1.
    """
    _wait(_popen(cmd))


@contextlib.contextmanager
def quiet() -> Yields[bool]:
    """Temporarily disable the noise generated by xtrace."""
    global debug
    orig, debug = debug, False
    yield orig
    debug = orig
