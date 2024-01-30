from __future__ import annotations

from .parse import Parse

P = Parse("A 1 2 1 3 1 2 1 Z")


class DescribeParse:
    def test_1(self) -> None:
        assert P.before.last("2", "1", " ") == "A 1 2 1 3"

    def test_2(self) -> None:
        assert P.before.last("2", "2") == P.before.first("2")

    def test_3(self) -> None:
        assert P.after.first("2", "1", " ") == "3 1 2 1 Z"

    def test_4(self) -> None:
        assert P.after.first("2", "2") == P.after.last("2")

    def test_21(self) -> None:
        assert P.after.first("1", " ").before.last("2", " ") == "2 1 3 1"

    def test_213(self) -> None:
        assert P.after.first(" ", " ").before.last("1", "1", " ") == "2 1 3"
