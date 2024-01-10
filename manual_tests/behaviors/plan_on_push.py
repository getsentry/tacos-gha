#!/usr/bin/env py.test
from __future__ import annotations

import datetime
import re

from lib.constants import NOW
from manual_tests.lib import tacos_demo
from manual_tests.lib.gh import gh
from manual_tests.lib.slice import Slice
from manual_tests.lib.slice import Slices


def test(
    pr: tacos_demo.PR,
    test_name: str,
    slices: Slices,
    user: str,
    repo: gh.LocalRepo,
) -> None:
    assert pr.get_plan()

    branch, message = tacos_demo.edit_slices(
        slices, test_name, message="more code"
    )

    gh.commit_and_push(repo, branch, message)
    plan = pr.get_plan()
    assert plan
    pattern = r"""\[([^\]]+)\]   \+ resource "null_resource" "edit-me" \{
\[[^\]]+\]       \+ id       = \(known after apply\)
\[[^\]]+\]       \+ triggers = \{
\[[^\]]+\]           \+ "now" = "([^"]+)"
\[[^\]]+\]         \}
\[[^\]]+\]     \}
"""
    found_slices: set[Slice] = set()
    # for every change found, make sure it's by the right user, that it covers
    # all the slices and has no extra.
    for match in re.finditer(pattern, plan):
        parts = match.group(1).split("/")
        w = "/".join(parts[-4:-1])
        s = parts[-1]
        assert w == f"terraform/env.{user}/prod"
        found_slices.add(Slice(s))
        t = datetime.datetime.fromisoformat(match.group(2))
        assert t > NOW
    assert (
        not slices.slices - found_slices and not found_slices - slices.slices
    )
