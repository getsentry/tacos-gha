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
    assertion: Assertion, limit: int = WAIT_LIMIT, sleep: int = WAIT_SLEEP
) -> None:
    # log the first try noisily
    print("LIMIT:", limit)
    if try_(assertion):
        return

    orig_limit = limit
    with sh.quiet():
        while limit >= 0:
            do_sleep(sleep)
            limit -= sleep

            if try_(assertion):
                return
        else:
            raise TimeoutExpired(
                f"never succeeded, over {orig_limit} seconds: {assertion}"
            )
