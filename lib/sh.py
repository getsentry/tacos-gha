#!/usr/bin/env py.test
from __future__ import annotations

import typing
from os import environ
from subprocess import CalledProcessError as CalledProcessError
from subprocess import TimeoutExpired as TimeoutExpired
from typing import TYPE_CHECKING
from typing import Iterator
from typing import MutableMapping
from typing import TypeVar

from . import json as JSON
from .sh_io import banner as banner
from .sh_io import info as info
from .sh_io import quiet as quiet
from .sh_io import xtrace

US_ASCII = "US-ASCII"  # the least-ambiguous encoding


if TYPE_CHECKING:
    # strict encapsulation: limit run-time access to just one function each
    from subprocess import CompletedProcess
    from subprocess import Popen

# TODO: centralize reused type aliases
Command = tuple[object, ...]
Yields = Iterator
Line = str  # blank lines and lines starting with # are not emitted
T = TypeVar("T")
Generator = typing.Generator[T, None, None]  # shim py313/PEP696


def cd(
    dirname: str, direnv: bool = True, env: MutableMapping[str, str] = environ
) -> None:
    from os import chdir

    xtrace(("cd", dirname))
    chdir(dirname)
    # TODO: set env[PWD] to absolute path
    if direnv:
        run(("direnv", "allow"))
        direnv_json: JSON.Value = json(("direnv", "export", "json"))
        if not isinstance(direnv_json, dict):
            raise AssertionError(f"expected dict, got {type(direnv_json)}")
        for key, value in direnv_json.items():
            if value is None:
                env.pop(key, None)
            else:
                assert isinstance(value, str), value
                env[key] = value


def stdout(cmd: Command) -> str:
    r"""Get the output of a command.

    Trailing newlines are stripped for convenience.

    >>> stdout(("echo", "ok"))
    'ok'
    """
    return _wait(_popen(cmd, capture_output=True)).stdout.rstrip("\n")


def json(cmd: Command) -> JSON.Value:
    """Parse the (singular) json on a subprocess' stdout.

    >>> json(("echo", '{"a": "b", "c": 3}'))
    {'a': 'b', 'c': 3}
    """
    import json

    result: JSON.Value = json.loads(stdout(cmd))
    return result


def lines(cmd: Command, *, encoding: str = US_ASCII) -> Generator[Line]:
    """Yield each object from newline-delimited json on a subprocess' stdout.

    >>> list(lines(("seq", 3, -1, 1)))
    ['3', '2', '1']
    """
    process = _popen(cmd, encoding=encoding, capture_output=True)
    assert process.stdout, process.stdout
    for line in process.stdout:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        yield line


def jq(cmd: Command, *, encoding: str = US_ASCII) -> Generator[JSON.Value]:
    """Yield each object from newline-delimited json on a subprocess' stdout.

    >>> tuple(jq(("seq", 3)))
    (1, 2, 3)
    """
    import json

    for line in lines(cmd, encoding=encoding):
        try:
            result: JSON.Value = json.loads(line)
        except Exception as error:
            raise ValueError(f"bad JSON: {line!r}") from error
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
