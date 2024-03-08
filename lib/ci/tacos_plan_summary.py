#!/usr/bin/env python3
from __future__ import annotations

import typing
from typing import Callable
from typing import Collection
from typing import Iterable
from typing import NamedTuple
from typing import Self
from typing import Sequence
from typing import TypeVar

from lib.sh import sh
from lib.types import Boolish
from lib.types import Generator
from lib.types import OSPath
from lib.types import P

ExitCode = None | str | int
Line = str  # these lines have no trailing newline attached
Lines = Iterable[Line]
Log = Sequence[Line]
COMMENT_SIZE_LIMIT = 64 * 2**10
Sized = typing.TypeVar("Sized", bound=typing.Sized)
T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


def get_file(path: OSPath) -> str:
    return path.read_text().strip()


def ensmallen(lines: Lines, size_limit: int) -> Generator[Line]:
    """Skip the middle portion of several lines if above the size size_limit."""
    from itertools import chain

    bufsize = 0
    lines = iter(lines)

    for line in lines:
        linelen = len(line) + 1
        if bufsize + linelen > size_limit * 1 / 3:
            lines = chain(reversed(tuple(lines)), [line])
            break

        yield line
        bufsize += linelen
    else:
        lines = []

    end_buffer: list[Line] = []
    for line in lines:
        linelen = len(line) + 1
        if bufsize + linelen > size_limit * 2 / 3:
            lines = reversed([line, *lines])
            break

        end_buffer.append(line)
        bufsize += linelen
    else:
        lines = []

    middle_buffer = list(lines)
    middle_size = sum(len(line) + 1 for line in middle_buffer)
    if bufsize + middle_size <= size_limit:
        yield from middle_buffer
    else:
        middle_summary = f"""\
...
( {middle_size / 1000:.1f}KB, {len(middle_buffer)} lines skipped )
..."""
        if len(middle_summary) < middle_size:
            yield from middle_summary.split("\n")
        else:
            yield from middle_buffer

    yield from reversed(end_buffer)


def gha_summary_and_details(
    summary: str, details: Iterable[str], rollup: Boolish = True
) -> Generator[str]:
    if rollup:
        yield "<details>"
        yield f"  <summary>{summary}</summary>"
    else:
        yield f"  {summary}"

    yield from details

    if rollup:
        yield "</details>"


def get_lines(path: OSPath) -> Log:
    return tuple(sh.stdout(("uncolor", path)).strip().splitlines())


class SliceSummary(NamedTuple):
    name: str
    tf_log: Log
    console_log: Log
    tacos_verb: str
    explanation: str
    returncode: int

    @classmethod
    def from_matrix_fan_out(cls, path: OSPath) -> Self:
        # convert a bunch of files into something well-typed

        return cls(
            name=get_file(path / "env/TF_ROOT_MODULE"),
            tf_log=get_lines(path / "tf-log.hcl"),
            console_log=get_lines(path / "console.log"),
            tacos_verb=get_file(path / "tacos_verb"),
            explanation=get_file(path / "explanation"),
            returncode=int(get_file(path / "returncode")),
        )

    @classmethod
    def from_matrix_fan_in(cls, path: OSPath) -> Generator[Self]:
        for matrix in (path / "matrix.list").open():
            matrix = matrix.strip()

            yield cls.from_matrix_fan_out(path / matrix)

    @property
    def dirty(self) -> bool:
        """The tf-plan is nonempty."""
        return self.returncode == 2

    @property
    def clean(self) -> bool:
        """The tf-plan is empty."""
        return self.returncode == 0

    @property
    def error(self) -> bool:
        return self.returncode not in (0, 2)

    def summarize_exit(self) -> tuple[bool, str]:
        if self.returncode == 0:
            return True, "success"
        elif self.tacos_verb == "plan" and self.returncode == 2:
            return True, "success, tfplan todo"
        else:
            return False, f"error code {self.returncode}"

    def summary(self) -> str:
        for line in reversed(self.tf_log):
            for success in ("Apply complete", "Plan:", "No changes"):
                if success in line:
                    return line  # :D

        for line in self.console_log:
            if "error" in line.lower():
                return line  # D:

        for line in reversed(self.console_log):
            lowered = line.lower()
            if "success" in lowered:
                return line  # :D
            elif "failure" in lowered:
                return line  # D:

        # we didn't find anything significant-looking at all
        _, summary = self.summarize_exit()
        return summary

    def markdown(
        self, size_budget: float, rollup: Boolish = True
    ) -> Generator[Line]:
        yield ""
        yield f"### {self.name}"
        if self.explanation:
            yield self.explanation
        yield ""

        yield from gha_summary_and_details(
            summary=self.summary(),
            details=self.markdown_details(
                rollup=rollup, size_budget=size_budget / 2
            ),
            rollup=rollup,
        )

        yield self.tag
        yield ""

    @property
    def tag(self) -> str:
        return f'<!-- getsentry/tacos-gha "{self.tacos_verb}({self.name})" -->'

    def markdown_details(
        self, size_budget: float, rollup: Boolish
    ) -> Generator[Line]:
        success, summary = self.summarize_exit()

        size_budget -= 1000

        yield from gha_summary_and_details(
            summary=f"Commands: ({summary})",
            details=(
                "",
                "```console",
                *ensmallen(self.console_log, size_limit=int(size_budget / 2)),
                "```",
            ),
            rollup=rollup or self.tf_log or success,
        )

        if not self.tf_log and not success:
            return

        yield "  Result:"
        if self.tf_log:
            yield ""
            yield "```hcl"
            yield from ensmallen(self.tf_log, size_limit=int(size_budget / 2))
            yield "```"
        else:
            yield "(no output)"

    def __str__(self) -> str:
        return self.name


def lines_length(lines: Collection[Line]) -> int:
    return sum(len(line) + 1 for line in lines)


def totalled(
    generator: Callable[P, Iterable[Sized]],
) -> Callable[P, typing.Generator[Sized, None, int]]:
    def wrapped(
        *args: P.args, **kwargs: P.kwargs
    ) -> typing.Generator[Sized, None, int]:
        total = 0
        for x in generator(*args, **kwargs):
            yield x
            total += len(x)
        return total

    return wrapped


@totalled
def header(
    error: Collection[SliceSummary],
    dirty: Collection[SliceSummary],
    clean: Collection[SliceSummary],
) -> Lines:
    slices = len(error) + len(dirty) + len(clean)
    yield f"# Terraform Plan"
    yield f"TACOS generated a terraform plan for {slices} slices:"
    yield f""

    if error:
        yield f"  * {len(error)} slices failed to plan"
    if dirty:
        yield f"  * {len(dirty)} slices have pending changes to apply"
    if clean:
        yield f"  * {len(clean)} slices are unaffected"


@totalled
def footer(clean: Collection[SliceSummary]) -> Lines:
    if not clean:
        return

    yield ""
    yield "## Clean"
    yield "These slices are in scope of your PR, but Terraform"
    yield "found no infra changes are currently necessary:"
    for slice in clean:
        yield f"  * {slice.name}"
    for slice in clean:
        yield slice.tag


@totalled
def error_sections(
    error: Collection[SliceSummary], size_budget: int, section_count: int
) -> Lines:
    if not error:
        return

    # FIXME: write to a file
    yield ""
    yield "## Errors"

    first = True
    for slice in error:
        # present the first error (only) expanded
        for line in slice.markdown(
            rollup=not first,
            size_budget=(
                size_budget if first else size_budget / section_count
            ),
        ):
            yield line
            size_budget -= len(line)
        section_count -= 1
        first = False


@totalled
def dirty_sections(dirty: Collection[SliceSummary], size_budget: int) -> Lines:
    if not dirty:
        return

    yield ""
    yield "## Changes"

    section_count = len(dirty)
    for slice in dirty:
        for line in slice.markdown(size_budget=size_budget / section_count):
            yield line
            size_budget -= len(line)
        section_count -= 1


class ValuedGenerator(typing.Generic[T, U, V]):
    value: V | None = None

    def __init__(self, generator: typing.Generator[T, U, V]):
        self.generator = generator
        super().__init__()

    def __iter__(self) -> typing.Generator[T, U, None]:
        self.value = yield from self.generator


def tacos_plan_summary(
    slices: Collection[SliceSummary], size_budget: int
) -> Generator[Line]:
    error = tuple(slice for slice in slices if slice.error)
    dirty = tuple(slice for slice in slices if slice.dirty)
    clean = tuple(slice for slice in slices if slice.clean)

    footer_lines = list(gen := ValuedGenerator(footer(clean)))
    assert gen.value is not None

    size_budget -= gen.value
    assert size_budget >= 0, size_budget

    size_budget -= yield from header(error, dirty, clean)
    assert size_budget >= 0, size_budget

    size_budget -= yield from error_sections(
        error, size_budget, section_count=len(error) + len(dirty)
    )
    # assert size_budget >= 0, size_budget

    size_budget -= yield from dirty_sections(dirty, size_budget)
    # assert size_budget >= 0, size_budget

    yield from footer_lines


def main() -> ExitCode:
    from sys import argv

    try:
        arg = argv[1]
    except IndexError:
        arg = "./matrix-fan-out"

    path = OSPath(arg)
    slices = tuple(SliceSummary.from_matrix_fan_in(path))
    size_budget = COMMENT_SIZE_LIMIT - 1000

    for line in tacos_plan_summary(slices, size_budget):
        print(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
