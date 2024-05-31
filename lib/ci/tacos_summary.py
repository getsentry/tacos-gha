from __future__ import annotations

from typing import Callable
from typing import Collection
from typing import Iterable
from typing import NamedTuple
from typing import Self
from typing import Sequence

from lib.byte_budget import BudgetError
from lib.byte_budget import ByteBudget
from lib.byte_budget import Line
from lib.byte_budget import Lines
from lib.byte_budget import Log
from lib.sh import sh

# from lib.types import Generator
from lib.types import Boolish
from lib.types import ExitCode
from lib.types import OSPath

COMMENT_SIZE_LIMIT = 64 * 2**10
SKIPPED_MESSAGE = "* ({count} more slices not shown)"
GHA_RUN_URL = "https://github.com/{}/actions/runs/{}"
FILE_NOT_FOUND = "(file not found: {!r}"

SectionFunction = Callable[[Sequence["SliceSummary"], int], Lines]
TacosSummary = Callable[
    [Collection["SliceSummary"], ByteBudget, str, int], Lines
]


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
        yield summary

    yield from details

    if rollup:
        yield "</details>"


def get_file(path: OSPath, default: str = FILE_NOT_FOUND) -> str:
    try:
        return path.read_text().strip()
    except FileNotFoundError:
        return default.format(path.name)


def get_lines(path: OSPath) -> Log:
    try:
        return tuple(sh.stdout(("uncolor", path)).strip().splitlines())
    except Exception as error:
        if not path.exists():
            return [FILE_NOT_FOUND.format(path.name)]
        else:
            return [str(error)]


class SliceSummary(NamedTuple):
    name: str
    tf_log: Log
    console_log: Log
    tacos_verb: str
    explanation: str
    returncode: int
    url: str

    @classmethod
    def from_matrix_fan_out(cls, path: OSPath) -> Self:
        # convert a bunch of files into something well-typed

        return cls(
            name=get_file(path / "env/TF_ROOT_MODULE"),
            tf_log=get_lines(path / "tf-log.hcl"),
            console_log=get_lines(path / "console.log"),
            tacos_verb=get_file(path / "tacos_verb"),
            explanation=get_file(path / "explanation"),
            returncode=int(get_file(path / "returncode", default="-1")),
            url=get_file(path / "url", default=""),
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
        """The job succeeded."""
        if self.tacos_verb == "apply":
            if (
                "No changes. Your infrastructure matches the configuration."
                in self.tf_log
            ):
                return self.returncode == 0
            else:
                return False
        else:
            return self.returncode == 0

    @property
    def applied(self) -> bool:
        """The job succeeded and made changes."""
        if (
            self.tacos_verb == "apply"
            and "Terraform will perform the following actions:" in self.tf_log
        ):
            return self.returncode == 0
        else:
            return False

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
            for success in (
                "Apply complete",
                "Plan:",
                "No changes",
                "success",
            ):
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
        is_success, summary = self.summarize_exit()
        if is_success:
            return f"Success: {summary}"
        else:
            return f"Failure: {summary}"

    def markdown(self, budget: ByteBudget, rollup: Boolish = True) -> Lines:
        budget -= 150  # account for static output
        budget.lines([self.explanation, self.tag, self.url])
        details = budget.generator(self.markdown_details, rollup=rollup)
        lines = gha_summary_and_details(
            summary=self.summary(), details=details, rollup=rollup
        )

        yield ""
        header = self.tag
        if self.url:
            header = f"[{header}]({self.url})"
        yield f"### {header}"
        if self.explanation:
            yield self.explanation
        yield ""
        yield from lines
        yield ""

    @property
    def tag(self) -> str:
        return f"{self.name} <!--🌮:{self.tacos_verb}-->"

    def markdown_details(self, budget: ByteBudget, rollup: Boolish) -> Lines:
        # budget -= 200  # account for static output
        success, summary = self.summarize_exit()
        show_results = self.tf_log or success

        if not self.tf_log or not success:
            share = 1 / 2 if show_results else 1
            yield from budget.lines(
                gha_summary_and_details(
                    summary=f"Commands: ({summary})",
                    details=(
                        "",
                        "```console",
                        # NB: careful not to account these lines twice
                        *ensmallen(
                            self.console_log, size_limit=int(budget * share)
                        ),
                        "```",
                    ),
                    rollup=rollup or self.tf_log or success,
                )
            )

        if not self.tf_log and not success:
            return

        if self.tf_log:
            yield ""
            yield "```hcl"
            yield from ensmallen(self.tf_log, size_limit=int(budget / 2))
            yield "```"
        else:
            yield "(no output)"

    def __str__(self) -> str:
        return self.tag


def mksection(
    budget: ByteBudget,
    slices: Collection[SliceSummary],
    title: str,
    first: bool = False,
    explanation: Log = (),
) -> Lines:
    if not slices:
        return

    further_header = [
        f"### Further {title}",
        "These slices' logs could not be shown due to size limits.",
    ]

    yield from budget.lines(("", f"## {title}"))
    yield from budget.lines(explanation)

    # account for static output
    budget.lines(further_header)
    budget.lines([SKIPPED_MESSAGE])

    section_count = len(slices)
    further: list[Line] = []
    for i, slice in enumerate(slices):
        # present (only) the first error expanded
        first = first and (i == 0)

        try:
            yield from budget.generator(
                slice.markdown, share=1 / section_count, rollup=not first
            )

        except BudgetError:
            try:
                further.extend(budget.lines([f"* {slice.tag}"]))
            except BudgetError:
                further.append(SKIPPED_MESSAGE.format(count=len(slices) - i))
                break

        else:
            first = False
            section_count -= 1

    if further:
        yield f"### Further {title}"
        yield "These slices' logs could not be shown due to size constraints."
        yield from further


def error_section(
    budget: ByteBudget, slices: Collection[SliceSummary]
) -> Lines:
    return mksection(budget, slices, title="Errors", first=True)


def process_matrix_fan_out(
    tacos_summary: TacosSummary, matrix_fan_out: OSPath
) -> Iterable[Line]:
    path = OSPath(matrix_fan_out)
    slices = tuple(SliceSummary.from_matrix_fan_in(path))
    budget = ByteBudget(COMMENT_SIZE_LIMIT - 1000)

    from os import environ

    run_id = int(environ["GITHUB_RUN_ID"])
    repository = environ["GITHUB_REPOSITORY"]

    return tacos_summary(slices, budget, repository, run_id)


def main_helper(tacos_summary: TacosSummary) -> ExitCode:
    from sys import argv

    try:
        arg = argv[1]
    except IndexError:
        arg = "./matrix-fan-out"

    for line in process_matrix_fan_out(tacos_summary, OSPath(arg)):
        print(line)

    return 0
