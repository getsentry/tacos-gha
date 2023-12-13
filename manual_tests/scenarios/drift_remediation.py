#!/usr/bin/env py.test
from __future__ import annotations

from lib.sh import sh
from manual_tests.lib import tacos_demo


def test(pr: tacos_demo.PR) -> None:
    sh.banner("somebody changes infrastructure out of band")
    sh.banner("pretend an hour passed: trigger the drift-scan job")
    sh.banner("check out automatically-created PR")
    sh.banner("edit and/or apply till plan is clean")
    sh.banner("request unlock")
