#!/usr/bin/env -S python3 -P
from __future__ import annotations

from typing import Collection

from lib.byte_budget import BudgetError
from lib.byte_budget import ByteBudget
from lib.byte_budget import Lines
from lib.byte_budget import Log
from lib.types import ExitCode

from .tacos_summary import GHA_RUN_URL
from .tacos_summary import SKIPPED_MESSAGE
from .tacos_summary import SliceSummary
from .tacos_summary import error_section
from .tacos_summary import main_helper


def header(
    error: Collection[SliceSummary],
    success: Collection[SliceSummary],
    repository: str,
    run_id: int,
) -> Log:
    slices = len(error) + len(success)

    result = [
        f"# [Terraform Unlock]({GHA_RUN_URL.format(repository, run_id)})",
        f"TACOS unlocked {slices} terraform slices:",
        f"",
    ]

    if error:
        result.append(f"* {len(error)} slices failed to unlock")
    if success:
        result.append(f"* {len(success)} slices successfully unlocked")

    return result


def unlock_success_section(
    budget: ByteBudget, slices: Collection[SliceSummary]
) -> Lines:
    if not slices:
        return

    yield from budget.lines(("", "## Success"))
    budget.lines(SKIPPED_MESSAGE)
    for i, slice in enumerate(slices):
        try:
            yield from budget.lines([f"* {slice}"])
        except BudgetError:
            yield SKIPPED_MESSAGE.format(count=len(slices) - i)
            return


def tacos_unlock_summary(
    slices: Collection[SliceSummary],
    budget: ByteBudget,
    repository: str,
    run_id: int,
) -> Lines:
    error = tuple(slice for slice in slices if slice.error)
    success = tuple(slice for slice in slices if slice.clean)

    # generate the more important "error" section last, so it can use any
    # slack left by the other sections.
    yield from budget.lines(header(error, success, repository, run_id))
    clean_lines = budget.generator(
        unlock_success_section, slices=success, share=1 / 2
    )
    error_lines = budget.generator(error_section, slices=error, share=1 / 1)
    assert 0 <= budget, budget

    yield from error_lines
    yield from clean_lines


def main() -> ExitCode:
    return main_helper(tacos_unlock_summary)


if __name__ == "__main__":
    raise SystemExit(main())
