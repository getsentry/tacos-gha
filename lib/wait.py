from __future__ import annotations

from os import getenv
from time import sleep as do_sleep
from typing import Callable

from lib import sh

WAIT_LIMIT = int(getenv("WAIT_LIMIT", "60"))
WAIT_SLEEP = int(getenv("WAIT_SLEEP", "3"))

Assertion = Callable[[], None | bool]


class TimeoutExpired(Exception):
    pass


def try_(assertion: Assertion) -> bool:
    try:
        result = assertion()
    except AssertionError:
        return False

    return result in (True, None)


def for_(
    assertion: Assertion, timeout: int | None = None, sleep: int = WAIT_SLEEP
) -> None:
    if timeout is None:
        timeout = WAIT_LIMIT
    # log the first try noisily
    if try_(assertion):
        return

    limit = timeout
    with sh.quiet():
        while limit >= 0:
            do_sleep(sleep)
            limit -= sleep

            if try_(assertion):
                return
        else:
            raise TimeoutExpired(
                f"never succeeded, over {timeout} seconds: {assertion}"
            )
