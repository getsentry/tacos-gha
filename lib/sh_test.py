#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from . import sh


class DescribeBanner:
    def its_pretty(self, capfd: pytest.CaptureFixture[str]) -> None:
        sh.banner("one:", 1)

        result = capfd.readouterr()
        assert result.out == ""
        assert result.err == "\x1b[92;1m ======== one: 1 ======== \x1b[m\n"


class DescribeJq:
    def it_handles_blank_lines(self) -> None:
        result = tuple(sh.jq(("echo", "1\n\n2")))
        assert result == (1, 2)

    def it_handles_commented_lines(self) -> None:
        result = tuple(sh.jq(("echo", "1\n#2\n3")))
        assert result == (1, 3)

    def it_throws_on_error(self) -> None:
        with pytest.raises(ValueError) as raised:
            tuple(sh.jq(("echo", "wut")))

        assert raised.value.args == ("bad JSON:\n    wut",)


_wait = sh._wait  # pyright:ignore[reportPrivateUsage]
_popen = sh._popen  # pyright:ignore[reportPrivateUsage]


class DescribePrivateWait:
    def it_can_timeout(self) -> None:
        proc = _popen(("sleep", 9999))
        with pytest.raises(sh.TimeoutExpired) as raised:
            _wait(proc, timeout=0.01)

        error = raised.value
        assert error.cmd == ("sleep", "9999")

    def it_can_raise_error(self) -> None:
        proc = _popen(("sh", "-c", "exit 33"))
        with pytest.raises(sh.CalledProcessError) as raised:
            _wait(proc)

        error = raised.value
        assert error.returncode == 33

    def it_can_ignore_error(self) -> None:
        proc = _popen(("sh", "-c", "exit 33"))
        result = _wait(proc, check=False)
        assert result.returncode == 33
