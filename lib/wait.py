from __future__ import annotations

from os import getenv
from time import sleep as do_sleep
from typing import Callable
from typing import TypeVar

from lib.sh import sh

WAIT_LIMIT = int(getenv("WAIT_LIMIT", "180"))
WAIT_SLEEP = int(getenv("WAIT_SLEEP", "3"))

# assertion is true when it returns a non-None object (without AssertionError)
T = TypeVar("T")
Assertion = Callable[[], T]


class TimeoutExpired(AssertionError):
    pass


def for_(
    assertion: Assertion[T], timeout: int = WAIT_LIMIT, sleep: int = WAIT_SLEEP
) -> T:
    # log the first try noisily
    try:
        return assertion()
    except AssertionError:
        pass  # let's try again

    limit = timeout
    with sh.quiet():
        while True:
            do_sleep(sleep)
            limit -= sleep

            try:
                return assertion()
            except AssertionError:
                if limit <= 0:
                    raise TimeoutExpired(
                        f"never succeeded, over {timeout} seconds: {assertion}"
                    )
