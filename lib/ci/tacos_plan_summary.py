#!/usr/bin/env python3
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
from .tacos_summary import mksection


def header(
    error: Collection[SliceSummary],
    dirty: Collection[SliceSummary],
    clean: Collection[SliceSummary],
    repository: str,
    run_id: int,
) -> Log:
    slices = len(error) + len(dirty) + len(clean)

    result = [
        f"# [Terraform Plan]({GHA_RUN_URL.format(repository, run_id)})",
        f"TACOS generated a terraform plan for {slices} slices:",
        f"",
    ]

    if error:
        result.append(f"* {len(error)} slices failed to plan")
    if dirty:
        result.append(f"* {len(dirty)} slices have pending changes to apply")
    if clean:
        result.append(f"* {len(clean)} slices are unaffected")

    return result


def dirty_section(
    budget: ByteBudget, slices: Collection[SliceSummary]
) -> Lines:
    return mksection(budget, slices, title="Changes", first=False)


def clean_section(
    budget: ByteBudget, slices: Collection[SliceSummary]
) -> Lines:
    if not slices:
        return

    yield from budget.lines((
        "",
        "## Clean",
        "These slices are in scope of your PR, but Terraform",
        "found no infra changes are currently necessary:",
    ))
    budget.lines(SKIPPED_MESSAGE)
    for i, slice in enumerate(slices):
        try:
            yield from budget.lines([f"* {slice}"])
        except BudgetError:
            yield SKIPPED_MESSAGE.format(count=len(slices) - i)
            return


def tacos_plan_summary(
    slices: Collection[SliceSummary],
    budget: ByteBudget,
    repository: str,
    run_id: int,
) -> Lines:
    error = tuple(slice for slice in slices if slice.error)
    dirty = tuple(slice for slice in slices if slice.dirty)
    clean = tuple(slice for slice in slices if slice.clean)

    # generate the more important "error" section last, so it can use any
    # slack left by the other sections.
    yield from budget.lines(header(error, dirty, clean, repository, run_id))
    clean_lines = budget.generator(clean_section, slices=clean, share=1 / 3)
    dirty_lines = budget.generator(dirty_section, slices=dirty, share=1 / 2)
    error_lines = budget.generator(error_section, slices=error, share=1 / 1)
    assert 0 <= budget, budget

    yield from error_lines
    yield from dirty_lines
    yield from clean_lines


def main() -> ExitCode:
    return main_helper(tacos_plan_summary)


if __name__ == "__main__":
    raise SystemExit(main())
