#!/usr/bin/env python3
from __future__ import annotations

from typing import Iterable
from typing import NamedTuple
from typing import Self

from lib.sh import sh
from lib.types import Boolish
from lib.types import Generator
from lib.types import OSPath

ExitCode = None | str | int
Line = str  # these lines have no trailing newline attached
Lines = Iterable[Line]
COMMENT_SIZE_LIMIT = 64 * 2**10


def get_file(path: OSPath) -> str:
    return path.read_text().strip()


def ensmallen(lines: Lines, limit: float) -> Generator[Line]:
    from itertools import chain

    bufsize = 0
    lines = iter(lines)

    for line in lines:
        linelen = len(line) + 1
        if bufsize + linelen > limit * 1 / 3:
            lines = chain(reversed(tuple(lines)), [line])
            break

        yield line
        bufsize += linelen
    else:
        lines = []

    end_buffer: list[Line] = []
    for line in lines:
        linelen = len(line) + 1
        if bufsize + linelen > limit * 2 / 3:
            lines = reversed([line, *lines])
            break

        end_buffer.append(line)
        bufsize += linelen
    else:
        lines = []

    middle_buffer = list(lines)
    middle_size = sum(len(line) + 1 for line in middle_buffer)
    if bufsize + middle_size <= limit:
        yield from middle_buffer
    else:
        yield "..."
        yield f"( {middle_size >> 10}KB, {len(middle_buffer)} lines skipped )"
        yield "..."

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


class SliceSummary(NamedTuple):
    name: str
    path: OSPath
    tacos_verb: str
    explanation: str
    returncode: int

    @classmethod
    def from_matrix_fan_out(cls, path: OSPath) -> Self:
        # convert a bunch of files into something well-typed
        return cls(
            name=get_file(path / "env/TF_ROOT_MODULE"),
            path=path,
            tacos_verb=get_file(path / "tacos_verb"),
            explanation=get_file(path / "explanation"),
            returncode=int(get_file(path / "returncode")),
        )

    @classmethod
    def from_matrix_fan_in(cls, path: OSPath) -> Generator[Self]:
        for matrix in (path / "matrix.list").open():
            matrix = matrix.strip()

            yield cls.from_matrix_fan_out(path / matrix)

    # see lib/ci/bin/tf-step-summary:
    @property
    def tf_log(self) -> OSPath:
        return self.path / "tf-log.hcl"

    @property
    def console_log(self) -> OSPath:
        return self.path / "console.log"

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
        log = tuple(sh.lines(("uncolor", self.tf_log)))
        for line in reversed(log):
            for success in ("Apply complete", "Plan:", "No changes"):
                if success in line:
                    return line  # :D

        log = tuple(sh.lines(("uncolor", self.console_log)))
        for line in log:
            if "error" in line.lower():
                return line  # D:

        for line in reversed(log):
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

        yield f'<!-- getsentry/tacos-gha "{self.tacos_verb}({self.name})" -->'
        yield ""

    def markdown_details(
        self, size_budget: float, rollup: Boolish
    ) -> Generator[Line]:
        tf_log = sh.stdout(("uncolor", self.tf_log)).strip()
        success, summary = self.summarize_exit()

        size_budget -= 1000

        yield from gha_summary_and_details(
            summary=f"Commands: ({summary})",
            details=(
                "",
                "```console",
                *ensmallen(
                    sh.stdout(("uncolor", self.console_log)).strip(),
                    limit=size_budget / 2,
                ),
                "```",
            ),
            rollup=rollup or tf_log or success,
        )

        if not tf_log and not success:
            return

        yield "  Result:"
        if tf_log:
            yield ""
            yield "```hcl"
            yield from ensmallen(tf_log, limit=size_budget / 2)
            yield "```"
        else:
            yield "(no output)"

    def __str__(self) -> str:
        return self.name


def tacos_plan_summary(path: OSPath) -> Generator[Line]:
    slices = tuple(SliceSummary.from_matrix_fan_in(path))

    dirty = tuple(slice for slice in slices if slice.dirty)
    clean = tuple(slice for slice in slices if slice.clean)
    error = tuple(slice for slice in slices if slice.error)

    # FIXME: write to a file
    yield "# Terraform Plan"
    yield f"TACOS generated a terraform plan for {len(slices)} slices:"
    yield ""
    if error:
        yield f"  * {len(error)} slices failed to plan"
    if dirty:
        yield f"  * {len(dirty)} slices have pending changes to apply"
    if clean:
        yield f"  * {len(clean)} slices are unaffected"

    if error:
        # FIXME: write to a file
        yield ""
        yield "## Errors"

        first = True
        for slice in error:
            # present the first error (only) expanded
            yield from slice.markdown(
                rollup=not first, size_budget=0.8 * COMMENT_SIZE_LIMIT
            )
            first = False

    if dirty:
        # FIXME: write to a file
        yield ""
        yield "## Changes"
        for slice in dirty:
            yield from slice.markdown()

    # FIXME: write to a file
    if clean:
        yield ""
        yield "## Clean"
        yield "These slices are in scope of your PR, but Terraform"
        yield "found no infra changes are currently necessary:"
        for slice in clean:
            yield f"  * {slice.name}"


def main() -> ExitCode:
    from sys import argv

    try:
        arg = argv[1]
    except IndexError:
        arg = "./matrix-fan-out"

    path = OSPath(arg)

    for line in tacos_plan_summary(path):
        print(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
