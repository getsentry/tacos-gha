#!/usr/bin/env py.test
from __future__ import annotations

import pytest

from . import sh
from .core import _popen  # pyright:ignore[reportPrivateUsage]
from .core import _wait  # pyright:ignore[reportPrivateUsage]


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
