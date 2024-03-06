#!/usr/bin/env py.test
from __future__ import annotations

from pytest import fixture

from lib.functions import one
from lib.sh import sh
from spec.lib import tacos_demo
from spec.lib.gh import gh
from spec.lib.slice import Slices
from spec.lib.testing import assert_there_can_be_only_one


@fixture
def slices(slices: Slices) -> Slices:
    # maximize interleaving/racy weirdness, so we know it works out fine
    return slices.all


def test(
    slices: Slices, test_name: str, demo: gh.LocalRepo, tacos_branch: gh.Branch
) -> None:
    sh.banner(
        f"Winner and Loser race to open a PR for the same slices: {slices}"
    )
    with (
        tacos_demo.PR.opened_for_slices(
            slices, test_name, demo, tacos_branch, branch=1
        ) as pr1,
        tacos_demo.PR.opened_for_slices(
            slices, test_name, demo, tacos_branch, branch=2
        ) as pr2,
    ):
        # pick one slice arbitrarily to care about more than the rest
        focus = one(slices.random(count=1))
        sh.banner(f"focus on slice: {focus}")

        winner, loser = assert_there_can_be_only_one(focus, pr1, pr2)

        sh.banner("Winner closes their PR")
        since = winner.close()
        # this won't necessarily succeed, due to other slices
        winner.check("Terraform Unlock").wait()

        sh.banner("Loser gets the lock, using :taco::lock label")
        since = loser.add_label(
            ":taco::plan"  # FIXME: add, use a :taco::lock label
        )
        assert loser.check("Terraform Plan").wait(since).success
        loser.slices.assert_locked()

        sh.banner("Loser can now merge their PR (with review).")
        loser.approve(tacos_demo.get_reviewer())
        since = loser.merge()
        assert loser.check("Terraform Unlock").wait(since).success
        loser.slices.assert_unlocked()
