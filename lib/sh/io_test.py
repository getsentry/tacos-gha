#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from lib import ansi

from . import io


class DescribeBanner:
    def its_pretty(self, capfd: pytest.CaptureFixture[str]) -> None:
        io.banner("one:", 1)

        result = capfd.readouterr()
        assert result.out == ""
        assert result.err == "\x1b[92;1m ======== one: 1 ======== \x1b[m\n"


class DescribeXtrace:
    def it_prints(self, capfd: pytest.CaptureFixture[str]) -> None:
        io.xtrace(("ls", "1 2", 3, "4"))

        result = capfd.readouterr()
        assert result.out == ""
        assert result.err == f"+ {ansi.TEAL}${ansi.RESET} ls '1 2' 3 4\n"


class DescribeQuiet:
    def it_suppresses_xtrace(self, capfd: pytest.CaptureFixture[str]) -> None:
        with io.quiet():
            io.xtrace(("ls", "1 2", 3, "4"))

        result = capfd.readouterr()
        assert result.out == ""
        assert result.err == ""
