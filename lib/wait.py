from __future__ import annotations

from os import getenv
from time import sleep as do_sleep
from typing import Callable
from typing import TypeVar

from lib.sh import sh

# usual amount of time to complete a GHA job is 30s from push
WAIT_LIMIT = float(getenv("WAIT_LIMIT", "90"))
WAIT_SLEEP = float(getenv("WAIT_SLEEP", "3"))

# assertion is true when it returns a non-None object (without AssertionError)
T = TypeVar("T")
Assertion = Callable[[], T | None]


class TimeoutExpired(AssertionError):
    pass


def for_(
    assertion: Assertion[T],
    timeout: float = WAIT_LIMIT,
    sleep: float = WAIT_SLEEP,
) -> T:
    __tracebackhide__ = True

    # speed up sleeps if there's too few
    if sleep > timeout / 10:
        sleep = timeout / 10
    # we're not going to get much higher resolution than 100ms
    sleep = max(0.125, sleep)

    limit = timeout

    with sh.uniq():  # suppress repeated messages during the loop
        result = assertion()
        if result:
            return result

        while True:
            do_sleep(sleep)
            result = assertion()
            if result:
                return result

            # track overall time
            limit -= sleep
            if limit < 0:
                raise TimeoutExpired(
                    f"never succeeded, over {timeout} seconds"
                )
