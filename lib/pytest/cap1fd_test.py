from __future__ import annotations

import pytest
from _pytest.capture import CaptureFixture

from lib.sh import sh
from lib.types import Generator

# fixture
from .cap1fd import cap1fd as cap1fd


def capfd(
    logging: None, capfd: pytest.CaptureFixture[str]
) -> Generator[pytest.CaptureFixture[str]]:
    del logging
    yield capfd


class DescribeCaptureCombined:
    def it_combines_stderr(self, cap1fd: CaptureFixture[str]) -> None:
        sh.run(("sh", "-c", "echo stdout >&1; echo stderr >&2"))

        std = cap1fd.readouterr()
        print("STDOUT:\n", std.out)
        print("STDERR:\n", std.err)
        assert std.err == ""
        assert (
            std.out
            == """\
+ \x1b[36;1m$\x1b[m sh -c 'echo stdout >&1; echo stderr >&2'
stdout
stderr
"""
        )
