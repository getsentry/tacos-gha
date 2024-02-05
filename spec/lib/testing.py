from __future__ import annotations

from typing import Iterable

from lib.parse import Parse


def assert_sequence_in_log(log: str, sequence: Iterable[str]) -> Parse:
    not_found: list[str] = []
    log = Parse(log)
    for expected in sequence:
        if expected not in log:
            not_found.append(expected)
        log = log.after.first(expected)
    assert not not_found  # i.e. all were found
    return log
