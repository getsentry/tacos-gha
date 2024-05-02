#!/usr/bin/env -S python3.12 -P
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
    clean: Collection[SliceSummary],
    applied: Collection[SliceSummary],
    repository: str,
    run_id: int,
) -> Log:
    slices = len(error) + len(clean) + len(applied)

    result = [
        f"# [Terraform Apply]({GHA_RUN_URL.format(repository, run_id)})",
        f"TACOS ran terraform apply for {slices} slices:",
        f"",
    ]

    if error:
        result.append(f"* {len(error)} slices failed to apply")
    if applied:
        result.append(f"* {len(applied)} slices have been applied")
    if clean:
        result.append(f"* {len(clean)} slices are clean")

    return result


def applied_section(
    budget: ByteBudget, slices: Collection[SliceSummary]
) -> Lines:
    return mksection(budget, slices, title="Applied", first=True)


def clean_section(
    budget: ByteBudget, slices: Collection[SliceSummary]
) -> Lines:
    if not slices:
        return

    yield from budget.lines((
        "",
        "## Clean",
        "Hurray! These slices already match the infrastructure.",
        "Good job on keeping it clean. :cookie: ",
    ))
    budget.lines(SKIPPED_MESSAGE)
    for i, slice in enumerate(slices):
        try:
            yield from budget.lines([f"* {slice}"])
        except BudgetError:
            yield SKIPPED_MESSAGE.format(count=len(slices) - i)
            return


def tacos_apply_summary(
    slices: Collection[SliceSummary],
    budget: ByteBudget,
    repository: str,
    run_id: int,
) -> Lines:
    error = tuple(slice for slice in slices if slice.error)
    clean = tuple(slice for slice in slices if slice.clean)
    applied = tuple(slice for slice in slices if slice.applied)
    # generate the more important "error" section last, so it can use any
    # slack left by the other sections.
    yield from budget.lines(header(error, clean, applied, repository, run_id))
    clean_lines = budget.generator(clean_section, slices=clean, share=1 / 3)
    applied_lines = budget.generator(
        applied_section, slices=applied, share=1 / 2
    )
    error_lines = budget.generator(error_section, slices=error, share=1 / 1)
    assert 0 <= budget, budget

    yield from error_lines
    yield from applied_lines
    yield from clean_lines


def main() -> ExitCode:
    return main_helper(tacos_apply_summary)


if __name__ == "__main__":
    raise SystemExit(main())
