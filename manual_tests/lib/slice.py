from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from random import Random
from typing import Iterator
from typing import Self

from lib.functions import now
from lib.sh import sh
from lib.types import Generator

from .xfail import XFailed
from .xfail import XFails


class Slice(Path):
    """Relative path to a terraform slice"""

    def is_locked(self, workdir: Path) -> bool:
        with sh.cd(workdir / self):
            return sh.success(("terraform", "plan", "--lock=true"))

    def edit(self, workdir: Path) -> None:
        tf_path = self / "edit-me.tf"
        tf = f"""\
resource "null_resource" "edit-me" {{
  triggers = {{
    now   = "{now()}"
    slice = "{workdir/self}"
  }}
}}
"""
        with sh.cd(workdir):
            with tf_path.open("w") as f:
                f.write(tf)
            # NB: file is empty if added before close
            sh.run(("git", "add", tf_path))


@dataclass(frozen=True)
class Slices:
    workdir: Path
    slices: frozenset[Slice]

    @classmethod
    def from_path(cls, workdir: Path) -> Self:
        return cls(
            workdir=workdir,
            slices=frozenset(
                Slice(slice.relative_to(workdir))
                # TODO: search for .tf or terragrunt.hcl files
                # for now, we assume all direct child directories are slices
                for slice in workdir.glob(f"*/")
            ),
        )

    def random(self, seed: object = None, count: int | None = None) -> Self:
        random = Random(seed)
        if count is None:
            count = random.randint(1, len(self.slices))

        cls = type(self)
        slices = random.sample(tuple(self.slices), count)
        return cls(workdir=self.workdir, slices=frozenset(slices))

    def edit(self) -> None:
        for slice in self:
            slice.edit(self.workdir)

    def assert_locked(self, xfails: XFails | None = None) -> None:
        cls = type(self)
        for slice in cls.from_path(self.workdir):
            locked = slice.is_locked(self.workdir)
            should_lock = slice in self

            try:
                assert locked == should_lock, (locked, slice)
            except AssertionError:
                if xfails is None:
                    raise XFailed("locking not yet implemented")
                else:
                    # FIXME: actually do locking in our GHA "Obtain Lock" job
                    assert locked == False
                    xfails.append(
                        (
                            "assert locked == False",
                            (locked, should_lock, slice),
                        )
                    )

    def paths(self) -> Generator[Path]:
        for slice in self.slices:
            yield self.workdir / slice

    def __iter__(self) -> Iterator[Slice]:
        return iter(self.slices)

    def __sub__(self, other: Self) -> Self:
        assert self.workdir == other.workdir, (self, other)
        cls = type(self)
        return cls(self.workdir, self.slices - other.slices)

    def __contains__(self, other: Slice) -> bool:
        return other in self.slices

    def __str__(self) -> str:
        return ", ".join(str(slice) for slice in sorted(self.slices))
