from __future__ import annotations

from dataclasses import dataclass
from functools import total_ordering
from typing import Callable
from typing import Concatenate
from typing import Iterable
from typing import Sequence

from lib.types import P

Line = str  # these lines have no trailing newline attached
Log = Sequence[Line]  # often a list
Lines = Iterable[Line]  # often a generator


class BudgetError(ValueError):
    pass


def lines_totalled(lines: Lines) -> tuple[Log, int]:
    """Modify a Lines generator to also return the total character count."""

    total = 0
    result: list[Line] = []
    for line in lines:
        result.append(line)
        total += len(line) + 1
    return result, total


@total_ordering
@dataclass
class ByteBudget:
    """A helper to keep track of how many bytes have been used.

    This can be used as an integer in various contexts, and has one method to
    account for a list of lines and one to account for a generator-function of
    lines. Such functions should take a ByteBudget as their first argument.
    Both methods return the lines that were accounted.
    """

    def __init__(self, budget: int | float | ByteBudget):
        super().__init__()
        self._budget: int = int(budget)

    def __truediv__(self, other: float | int) -> ByteBudget:
        return ByteBudget(self._budget / other)

    def __mul__(self, other: float | int) -> ByteBudget:
        return ByteBudget(self._budget * other)

    def __int__(self) -> int:
        return self._budget

    def __sub__(self, other: float | int) -> ByteBudget:
        return ByteBudget(self._budget - other)

    def __isub__(self, other: float | int) -> ByteBudget:
        self._budget = int(self._budget - other)
        return self

    def __lt__(self, other: float | int | ByteBudget) -> bool:
        if isinstance(other, ByteBudget):
            return self._budget < other._budget
        else:
            return self._budget < other

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ByteBudget):
            return self._budget == other._budget
        elif isinstance(other, (int, float)):
            return self._budget == other
        else:
            return NotImplemented

    def generator(
        self,
        line_generator: Callable[Concatenate[ByteBudget, P], Lines],
        share: float = 1.0,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> Log:
        assert 0 <= share <= 1
        section_budget = self * share
        lines = line_generator(section_budget, *args, **kwargs)
        return self.lines(lines, share)

    def lines(self, lines: Lines, share: float = 1.0) -> Log:
        """Record lines already generated into the doc's size-budget."""
        section_budget = self * share
        lines, size = lines_totalled(lines)
        if size <= section_budget:
            self._budget -= size
            return lines
        else:
            raise BudgetError(size, section_budget)

    def __repr__(self) -> str:
        return f"ByteBudget({self._budget})"
