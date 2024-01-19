from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import TYPE_CHECKING

from lib.constants import EMPTY_PATH
from lib.functions import now
from lib.sh import sh
from lib.tacos.dependent_slices import TFCategorized
from lib.tf_lock import tf_lock
from lib.tf_lock.tf_lock import get_lock_info
from lib.types import Generator
from lib.types import OSPath
from lib.types import Path

if TYPE_CHECKING:
    from typing import Iterator
    from typing import Self


class Slice(Path):
    """Relative path to a terraform slice"""

    def is_locked(self) -> bool:
        lock, _ = get_lock_info(self)
        return lock is True

    def edit(self, workdir: OSPath) -> None:
        tf_path = self / "edit-me.tf"
        tf = f"""\
resource "null_resource" "edit-me" {{
  triggers = {{
    now = "{now()}"
  }}
}}
"""
        with sh.cd(workdir):
            with OSPath(tf_path).open("w") as f:
                f.write(tf)
            # NB: file is empty if added before close
            sh.run(("git", "add", tf_path))


@dataclass(frozen=True)
class Slices:
    workdir: OSPath
    slices: frozenset[Slice]

    @classmethod
    def from_path(cls, workdir: OSPath, subpath: Path = EMPTY_PATH) -> Self:
        tf_categorized = TFCategorized.from_git(workdir / subpath)
        return cls(
            workdir=workdir,
            slices=frozenset(
                Slice(subpath / slice) for slice in tf_categorized.slices
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

    def assert_locked(self) -> None:
        cls = type(self)
        for slice in cls.from_path(self.workdir):
            locked = slice.is_locked(self.workdir)
            should_lock = slice in self

            assert locked == should_lock, (locked, slice)

    def paths(self) -> Generator[Path]:
        for slice in self.slices:
            yield self.workdir / slice

    def force_unlock(self) -> None:
        """Unlock these slices, forcefully."""
        sh.banner("forcefully unlocking slices...")
        with sh.cd(self.workdir):
            for slice in self:
                tf_lock.force_unlock(slice)

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
