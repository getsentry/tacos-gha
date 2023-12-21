#!/usr/bin/env py.test
from __future__ import annotations

import datetime
import re

from lib.constants import NOW
from manual_tests.lib import tacos_demo
from manual_tests.lib.gh import gh
from manual_tests.lib.slice import Slices


def test(pr: tacos_demo.PR, test_name: str, slices: Slices) -> None:
    assert pr.get_plan()

    branch, message = tacos_demo.edit(slices, test_name, message="more code")

    gh.commit_and_push(slices.workdir, branch, message)
    plan = pr.get_plan()
    assert plan
    for slice in slices:
        pattern = rf"""  \+ resource "null_resource" "edit-me" \{{
      \+ id       = \(known after apply\)
      \+ triggers = \{{
          \+ "now"   = "([^"]+)"
          \+ "slice" = "{slices.workdir/slice}"
        \}}
    \}}
"""
        match = re.search(pattern, plan)
        assert match is not None
        t = datetime.datetime.fromisoformat(match.group(1))
        assert t > NOW
