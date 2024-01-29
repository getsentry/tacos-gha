from __future__ import annotations

from typing import Callable
from typing import ClassVar
from typing import Self

BEFORE = 0
AFTER = -1


class Parse(str):
    @property
    def before(self) -> ParseBefore:
        return ParseBefore(self)

    @property
    def after(self) -> ParseAfter:
        return ParseAfter(self)

    def between(self, left: str, right: str) -> Self:
        cls = type(self)
        return cls(self.after.first(left).before.last(right))

    def __repr__(self) -> str:
        return f"Parse({str(self)!r})"


class _Parse(Parse):
    _when: ClassVar[int]

    def _parse(
        self,
        split: Callable[[str, str, int], list[str]],
        separators: tuple[str, ...],
    ) -> Self:
        cls = type(self)
        val: str = self
        for sep in separators:
            val = split(val, sep, 1)[cls._when]
        return cls(val)

    def first(self, *sep: str) -> Self:
        return self._parse(str.split, sep)

    def last(self, *sep: str) -> Self:
        return self._parse(str.rsplit, sep)


class ParseBefore(_Parse):
    _when = BEFORE

    def __repr__(self) -> str:
        return super().__repr__() + ".before"


class ParseAfter(_Parse):
    _when = AFTER

    def __repr__(self) -> str:
        return super().__repr__() + ".after"
