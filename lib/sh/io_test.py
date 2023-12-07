from __future__ import annotations

import pytest

from . import io


class DescribeBanner:
    def its_pretty(self, capfd: pytest.CaptureFixture[str]) -> None:
        io.banner("one:", 1)

        result = capfd.readouterr()
        assert result.out == ""
        assert result.err == "\x1b[92;1m ======== one: 1 ======== \x1b[m\n"
