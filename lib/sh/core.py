#!/usr/bin/env py.test
# the core private functions (_popen, _wait) plus their direct callers
from __future__ import annotations

from typing import TYPE_CHECKING

from lib.functions import LessThanOneError as LessThanOneError
from lib.functions import MoreThanOneError as MoreThanOneError
from lib.functions import one
from lib.types import Environ
from lib.types import OSPath

from .constant import US_ASCII
from .io import xtrace
from .types import Command
from .types import Generator

# empty lines and lines beginning with '#' not returned
Line = str


if TYPE_CHECKING:
    # strict encapsulation: limit run-time access to just one function each
    from subprocess import CompletedProcess
    from subprocess import Popen


def get_HERE(__file__: str) -> OSPath:
    """Return the containing directory of a moudle, given its __file__.

    A substitute for the common HERE variable shell-scripting pattern.
    """
    return OSPath(__file__).parent.resolve()


def run(
    cmd: Command, env: Environ | None = None, input: str | None = None
) -> None:
    """Run a command to completion. Raises on error.

    >>> run(('echo', 'ok'))
    >>> run(('false', 'not ok'))
    Traceback (most recent call last):
        ...
    subprocess.CalledProcessError: Command '('false', 'not ok')' returned non-zero exit status 1.
    """
    _wait(_popen(cmd, env=env, input=input), input=input)


def stdout(cmd: Command) -> str:
    r"""Get the output of a command.

    Trailing newlines are stripped for convenience.

    >>> stdout(("echo", "ok"))
    'ok'
    """
    return _wait(_popen(cmd, capture_output=True)).stdout.rstrip("\n")


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

    # handle termination and error codes
    _wait(process)


def line(cmd: Command, *, encoding: str = US_ASCII) -> Line:
    """
    >>> line(('echo', 'ok'))
    'ok'
    """
    return one(lines(cmd, encoding=encoding))


def returncode(cmd: Command) -> int:
    """Run a command and report its exit code.

    >>> returncode(('true',))
    0
    >>> returncode(('sh', '-c', 'exit 33'))
    33
    """
    # any non-ascii bytes are ambiguous, here:
    result = _wait(_popen(cmd), check=False)
    return result.returncode


_returncode = returncode


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
    return _returncode(cmd) == returncode


def _stringify(o: object) -> str:
    if isinstance(o, bytes):
        return o.decode("US-ASCII")  # other bytes are ambiguous
    else:
        return str(o)


def _popen(
    cmd: Command,
    capture_output: bool = False,
    encoding: str = US_ASCII,
    env: Environ | None = None,
    input: str | None = None,
) -> Popen[str]:
    import subprocess

    xtrace(cmd)

    if cmd[0] == ":":
        # : is the POSIX-specified shell builtin for 'true', but we've no shell
        cmd = ("true",) + cmd[1:]

    if input is not None:
        stdin = subprocess.PIPE
    else:
        stdin = None

    if capture_output:
        stdout = subprocess.PIPE
    else:
        stdout = None

    from os import environ

    tmp = env
    env = environ.copy()
    if tmp:
        env.update(tmp)
    del tmp

    return subprocess.Popen(
        tuple(_stringify(arg) for arg in cmd),
        text=True,
        encoding=encoding,
        stdin=stdin,
        stdout=stdout,
        env=env,
        close_fds=False,
    )


def _wait(
    process: Popen[str],
    input: str | None = None,
    timeout: float | None = None,
    check: bool = True,
) -> CompletedProcess[str]:
    """Stolen from the last half of stdlib subprocess.run; finish a process."""
    import subprocess

    with process:
        try:
            stdout, stderr = process.communicate(input, timeout=timeout)
        except:  # Including KeyboardInterrupt, communicate handled that.
            process.kill()
            # We don't call process.wait() as .__exit__ does that for us.
            raise
        retcode = process.poll()
        if check and retcode:
            raise subprocess.CalledProcessError(
                retcode, process.args, output=stdout, stderr=stderr
            )
    assert retcode is not None, retcode
    return subprocess.CompletedProcess(process.args, retcode, stdout, stderr)
