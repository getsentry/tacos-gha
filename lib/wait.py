from __future__ import annotations

from os import getenv
from time import sleep as do_sleep
from typing import Callable

from lib import sh

WAIT_LIMIT = int(getenv("WAIT_LIMIT", "60"))
WAIT_SLEEP = int(getenv("WAIT_SLEEP", "3"))

Assertion = Callable[[], None | bool]


def _wait_loop(assertion: Assertion, limit: int, sleep: int) -> None:
    while limit >= 0:
        try:
            result = assertion()
        except AssertionError:
            result = False

        if result in (True, None):
            return

        do_sleep(sleep)
        limit -= sleep
    else:
        do_sleep(sleep)  # we're about to try one last time


def for_(
    assertion: Assertion, limit: int = WAIT_LIMIT, sleep: int = WAIT_SLEEP
) -> None:
    sh.banner(f"retrying for {limit} seconds...")
    with sh.quiet():
        _wait_loop(assertion, limit - sleep, sleep)
    sh.run((":", "show the final try:"))
    assertion()
