from __future__ import annotations

from os import getenv
from time import sleep as do_sleep
from typing import Callable
from typing import TypeVar

from lib.sh import sh

# usual amount of time to complete a GHA job is 30s from push
WAIT_LIMIT = int(getenv("WAIT_LIMIT", "90"))
WAIT_SLEEP = int(getenv("WAIT_SLEEP", "3"))

# assertion is true when it returns a non-None object (without AssertionError)
T = TypeVar("T")
Assertion = Callable[[], T | None]


class TimeoutExpired(AssertionError):
    pass


def for_(
    assertion: Assertion[T], timeout: int = WAIT_LIMIT, sleep: int = WAIT_SLEEP
) -> T:
    __tracebackhide__ = True

    # log the first try noisily
    result = assertion()
    if result:
        return result

    if timeout / sleep < 10:
        sleep = max(1, int(timeout / 10))

    limit = timeout

    with sh.uniq():  # suppress repeated messages during the loop
        while True:
            do_sleep(sleep)
            limit -= sleep

            result = assertion()
            if result:
                return result

            if limit <= 0:
                raise TimeoutExpired(
                    f"never succeeded, over {timeout} seconds"
                )
