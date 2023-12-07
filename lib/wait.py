from __future__ import annotations

from os import getenv
from time import sleep as do_sleep
from typing import Callable

from lib import sh

WAIT_LIMIT = int(getenv("WAIT_LIMIT", "60"))
WAIT_SLEEP = int(getenv("WAIT_SLEEP", "3"))

Assertion = Callable[[], None | bool]


def for_(
    assertion: Assertion, limit: int = WAIT_LIMIT, sleep: int = WAIT_SLEEP
) -> None:
    while limit >= sleep:
        try:
            with sh.quiet():
                result = assertion()
        except AssertionError:
            result = False

        if result in (True, None):
            return

        do_sleep(sleep)
        limit -= sleep
    else:
        sh.banner("last try")
        do_sleep(max(limit, 0))  # we're about to try one last time
        assertion()
