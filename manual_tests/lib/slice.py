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
from lib.types import OSPath
from lib.types import Path
from manual_tests.lib import tf

if TYPE_CHECKING:
    from typing import Iterator
    from typing import Self


class Slice(Path):
    """Relative path to a terraform slice"""

    def is_locked(self) -> bool:
        lock, _ = get_lock_info(self)
        return lock is True

    def edit(self, slices_path: OSPath) -> None:
        tf_path = self / "edit-me.tf"
        tf = f"""\
resource "null_resource" "edit-me" {{
  triggers = {{
    now = "{now()}"
  }}
}}
"""
        with sh.cd(slices_path):
            with OSPath(tf_path).open("w") as f:
                f.write(tf)
            # NB: file is empty if added before close
            sh.run(("git", "add", tf_path))


@dataclass(frozen=True)
class Slices:
    workdir: OSPath
    subpath: Path
    slices: frozenset[Slice]

    @property
    def path(self) -> OSPath:
        return self.workdir / self.subpath

    @classmethod
    def from_path(cls, workdir: OSPath, subpath: Path = EMPTY_PATH) -> Self:
        slices_path = workdir / subpath
        tf_categorized = TFCategorized.from_git(slices_path)
        return cls(
            workdir=workdir,
            subpath=subpath,
            slices=frozenset(Slice(slice) for slice in tf_categorized.slices),
        )

    def random(self, seed: object = None, count: int | None = None) -> Self:
        random = Random(seed)
        if count is None:
            count = random.randint(1, len(self.slices) - 1)

        cls = type(self)
        slices = random.sample(tuple(self.slices), count)
        return cls(
            workdir=self.workdir,
            subpath=self.subpath,
            slices=frozenset(slices),
        )

    def edit(self) -> None:
        for slice in self:
            slice.edit(self.path)

    @property
    def all(self) -> Self:
        cls = type(self)
        return cls.from_path(self.workdir, self.subpath)

    def assert_locked(self) -> None:
        for slice in self.all:
            locked = slice.is_locked()
            should_lock = slice in self

            assert locked == should_lock, (locked, slice)

    def assert_unlocked(self) -> None:
        for slice in self.all:
            assert not slice.is_locked()

    def force_unlock(self) -> None:
        """Unlock these slices, forcefully."""
        sh.banner("forcefully unlocking slices")
        with sh.cd(self.path):
            for slice in self:
                tf_lock.force_unlock(slice)

    def plan_is_clean(self) -> bool:
        with sh.cd(self.path):
            return tf.plan_is_clean(sorted(self))

    def apply(self) -> None:
        sh.banner("applying slices")
        with sh.cd(self.path):
            tf.apply(sorted(self))

    def force_clean(self) -> None:
        # cleanup: apply main in case the test left things in a dirty state
        sh.banner("cleanup: roll back any drift")
        sh.run(("git", "-C", self.path, "reset", "--hard", "origin/main"))
        self.force_unlock()
        self.apply()
        sh.banner("cleanup complete")

    def __iter__(self) -> Iterator[Slice]:
        return iter(self.slices)

    def __sub__(self, other: Self) -> Self:
        if (self.workdir, self.subpath) == (other.workdir, other.subpath):
            raise ValueError("can't subtract unrelated", self, other)

        cls = type(self)
        return cls(self.workdir, self.subpath, self.slices - other.slices)

    def __contains__(self, other: Slice) -> bool:
        return other in self.slices

    def __str__(self) -> str:
        result = ", ".join(str(slice) for slice in sorted(self.slices))
        if self.subpath:
            result = f"{self.subpath}: {result}"
        return result
