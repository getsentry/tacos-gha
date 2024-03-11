#!/usr/bin/env python3
from __future__ import annotations

from typing import Callable
from typing import Collection
from typing import Iterable
from typing import NamedTuple
from typing import Self
from typing import Sequence

from lib.sh import sh

# from lib.types import Generator
from lib.types import Boolish
from lib.types import OSPath
from lib.types import P

COMMENT_SIZE_LIMIT = 64 * 2**10

ExitCode = None | str | int
Line = str  # these lines have no trailing newline attached
Lines = Iterable[Line]  # often a generator
Log = Sequence[Line]  # often a list
SectionFunction = Callable[[Sequence["SliceSummary"], int], tuple[Lines, int]]


def totalled(generator: Callable[P, Lines]) -> Callable[P, tuple[Log, int]]:
    """Modify a Lines generator to also return the total character count."""

    def wrapped(*args: P.args, **kwargs: P.kwargs) -> tuple[Log, int]:
        total = 0
        result: list[Line] = []
        for line in generator(*args, **kwargs):
            result.append(line)
            total += len(line) + 1
        return result, total

    return wrapped


def lines_totalled(lines: Lines) -> tuple[Log, int]:
    """Modify a Lines generator to also return the total character count."""

    total = 0
    result: list[Line] = []
    for line in lines:
        result.append(line)
        total += len(line) + 1
    return result, total


def ensmallen(lines: Lines, size_limit: int) -> Lines:
    """Skip the middle portion of several lines if above the size size_limit."""
    bufsize = 0
    lines = iter(lines)

    for line in lines:
        linelen = len(line) + 1
        if bufsize + linelen > size_limit * 1 / 3:
            lines = reversed([line, *lines])
            break

        yield line
        bufsize += linelen

    end_buffer: list[Line] = []
    for line in lines:
        linelen = len(line) + 1
        if bufsize + linelen > size_limit * 2 / 3:
            lines = reversed([line, *lines])
            break

        end_buffer.append(line)
        bufsize += linelen

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
    summary: Line, details: Lines, rollup: Boolish = True
) -> Lines:
    if rollup:
        yield "<details>"
        yield f"<summary>{summary}</summary>"
    else:
        yield f"{summary}"

    yield from details

    if rollup:
        yield "</details>"


def get_file(path: OSPath) -> str:
    return path.read_text().strip()


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
    def from_matrix_fan_in(cls, path: OSPath) -> Iterable[Self]:
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

    @totalled
    def markdown(self, size_budget: int, rollup: Boolish = True) -> Lines:
        section_budget = size_budget - (
            int(len(self.explanation) + len(self.tag) + 100)
        )
        details = self.markdown_details(
            rollup=rollup, size_budget=section_budget
        )
        lines = gha_summary_and_details(
            summary=self.summary(), details=details, rollup=rollup
        )

        yield ""
        yield f"### {self.tag}"
        if self.explanation:
            yield self.explanation
        yield ""
        yield from lines
        yield ""

    @property
    def tag(self) -> str:
        return f"{self.name} <!--🌮:{self.tacos_verb}-->"

    def markdown_details(self, size_budget: int, rollup: Boolish) -> Lines:
        log, size = lines_totalled(
            ensmallen(self.console_log, size_limit=int(size_budget / 2) - 200)
        )
        size_budget -= size

        success, summary = self.summarize_exit()

        lines, size = lines_totalled(
            gha_summary_and_details(
                summary=f"Commands: ({summary})",
                details=("", "```console", *log, "```"),
                rollup=rollup or self.tf_log or success,
            )
        )
        size_budget -= size
        yield from lines

        if not self.tf_log and not success:
            return

        yield "  Result:"
        if self.tf_log:
            yield ""
            yield "```hcl"
            log, size = lines_totalled(
                ensmallen(self.tf_log, size_limit=int(size_budget / 2))
            )
            size_budget -= size
            yield from log
            yield "```"
        else:
            yield "(no output)"

    def __str__(self) -> str:
        return self.tag


@totalled
def header(
    error: Collection[SliceSummary],
    dirty: Collection[SliceSummary],
    clean: Collection[SliceSummary],
) -> Log:
    slices = len(error) + len(dirty) + len(clean)

    result = [
        f"# Terraform Plan",
        f"TACOS generated a terraform plan for {slices} slices:",
        f"",
    ]

    if error:
        result.append(f"  * {len(error)} slices failed to plan")
    if dirty:
        result.append(f"  * {len(dirty)} slices have pending changes to apply")
    if clean:
        result.append(f"  * {len(clean)} slices are unaffected")

    return result


def mksection(
    slices: Collection[SliceSummary],
    size_budget: int,
    title: str,
    first: bool = False,
) -> Lines:
    if not slices:
        return

    size_budget -= 150  # account for static output
    yield ""
    yield f"## {title}"

    section_count = len(slices)
    further: list[SliceSummary | str] = []
    results: list[Log] = []
    # for i, slice in reversed(tuple(enumerate(slices))):
    for i, slice in enumerate(slices):
        # present (only) the first error expanded
        first = first and (i == 0)
        section_budget = size_budget // section_count
        lines, size = slice.markdown(section_budget, rollup=not first)
        first = False
        section_count -= 1

        if size < section_budget:
            results.append(lines)
            size_budget -= size
            continue

        size_budget -= len(slice.tag) + 10
        if size_budget > 0:
            further.append(slice)
        else:
            further.append(f"({len(slices) - i} slices skipped due to size)")
            break

    # for lines in reversed(results):
    for lines in results:
        yield from lines

    if further:
        yield f"### Further {title}"
        yield "These slices' logs could not be shown due to size constraints."
        # for line in reversed(further):
        for line in further:
            yield f" * {line}"


@totalled
def error_section(slices: Collection[SliceSummary], size_budget: int) -> Lines:
    return mksection(slices, size_budget, title="Errors", first=True)


@totalled
def dirty_section(slices: Collection[SliceSummary], size_budget: int) -> Lines:
    return mksection(slices, size_budget, title="Changes", first=False)


@totalled
def clean_section(slices: Collection[SliceSummary], size_budget: int) -> Lines:
    if not slices:
        return

    size_budget -= 300  # account for static output
    yield ""
    yield "## Clean"
    yield "These slices are in scope of your PR, but Terraform"
    yield "found no infra changes are currently necessary:"
    for i, slice in enumerate(slices):
        size_budget -= len(slice.tag) + 3
        if size_budget > 0:
            yield f"  * {slice}"
        else:
            yield f"  * ({len(slices) - i} slices skipped, due to comment size)"
            break


def tacos_plan_summary(
    slices: Collection[SliceSummary], size_budget: int
) -> Lines:

    error = tuple(slice for slice in slices if slice.error)
    dirty = tuple(slice for slice in slices if slice.dirty)
    clean = tuple(slice for slice in slices if slice.clean)

    lines, size = header(error, dirty, clean)
    size_budget -= size
    yield from lines

    def budget(
        mksection: SectionFunction,
        slices: Sequence[SliceSummary],
        section_budget: float,
    ) -> Lines:
        nonlocal size_budget
        lines, size = mksection(slices, int(section_budget))
        if size > section_budget:
            raise AssertionError(size, section_budget)
        size_budget -= size
        return lines

    clean_lines = budget(clean_section, clean, size_budget / 3)
    dirty_lines = budget(dirty_section, dirty, size_budget / 2)
    error_lines = budget(error_section, error, size_budget / 1)

    assert size_budget >= 0, size_budget

    yield from error_lines
    yield from dirty_lines
    yield from clean_lines


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
