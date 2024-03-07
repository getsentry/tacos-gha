from __future__ import annotations

from typing import Iterable

from lib.parse import Parse
from lib.sh import sh
from spec.lib import tacos_demo
from spec.lib.slice import Slice

# TODO: improve the conflict message: "lock failed, on slice prod/slice-3-vm, due to user1, PR #334 "
CONFLICT_MESSAGE = """
$ sudo-gcp tf-lock-acquire
You are authenticated for the next hour as: tacos-gha-tf-state-admin@sac-dev-sa.iam.gserviceaccount.com
tf-lock-acquire: failure: not """


def assert_sequence_in_log(log: str, sequence: Iterable[str]) -> Parse:
    not_found: list[str] = []
    log = Parse(log)
    for expected in sequence:
        if expected not in log:
            not_found.append(expected)
        log = log.after.first(expected)
    assert not not_found  # i.e. all were found
    return log


def assert_there_can_be_only_one(
    slice: Slice, *prs: tacos_demo.PR
) -> tuple[tacos_demo.PR, tacos_demo.PR]:
    sh.banner(f"Slice: {slice}")

    winner = loser = None
    for pr in prs:
        comments = pr.get_comments_for_job("plan")
        check = pr.check(
            "Terraform Plan", f"TACOS Plan ({pr.slices.subpath / slice})"
        ).ran()
        assert check is not None
        if check.conclusion == "SUCCESS":
            winner = pr
            print("Winner:", winner)
            assert CONFLICT_MESSAGE not in comments[slice]
        elif check.conclusion == "FAILURE":
            loser = pr
            print("Loser:", loser)
            assert CONFLICT_MESSAGE in comments[slice]
        else:
            raise AssertionError(check)

    # for some particular slice, there's one winner and one loser
    assert None not in (winner, loser)

    # pyright wants more-specific assertions
    assert winner is not None, winner
    assert loser is not None, loser

    return winner, loser
