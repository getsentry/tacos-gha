from __future__ import annotations

import contextlib
from os import getenv

from lib import ansi

from .types import Command
from .types import Generator

PS4 = f"+ {ansi.TEAL}${ansi.RESET} "


debug: bool = bool(getenv("DEBUG", "1"))


def info(*msg: object) -> None:
    """Show the user a message."""

    from sys import stderr

    print(*msg, file=stderr, flush=True)


def banner(*msg: object) -> None:
    """Show a colorized, high-visibility message."""
    info(ansi.GREEN, "=" * 8, *msg, "=" * 8, ansi.RESET)


def quote(cmd: Command) -> str:
    """Escape a command to copy-pasteable shell form.

    >>> print(quote(("ls", "1 2", 3, "4")))
    ls '1 2' 3 4
    """
    import shlex

    return " ".join(shlex.quote(str(arg)) for arg in cmd)


def xtrace(cmd: Command) -> None:
    """Simulate bash's xtrace: show a command with copy-pasteable escaping.

    Output is suppressed when `sh.debug` is False.
    """
    if debug:
        info("".join((PS4, quote(cmd))))


@contextlib.contextmanager
def quiet() -> Generator[bool]:
    """Temporarily disable the noise generated by xtrace."""
    global debug
    orig, debug = debug, False
    yield orig
    debug = orig