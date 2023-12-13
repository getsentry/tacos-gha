from __future__ import annotations

from pathlib import Path
from random import Random
from typing import ContextManager
from typing import Self

from lib.functions import now
from lib.functions import one
from lib.sh import sh

from .xfail import XFails


class Slice(int):
    @property
    def directory(self) -> Path:
        return one(Path.cwd().glob(f"slice-{self}*/"))

    def chdir(self) -> ContextManager[Path]:
        return sh.cd(self.directory)

    def is_locked(self) -> bool:
        with self.chdir():
            return sh.success(("terraform", "plan", "--lock=true"))

    def edit(self) -> None:
        tf_path = self.directory / "edit-me.tf"
        tf = f"""\
resource "null_resource" "edit-me" {{
  triggers = {{
    now = "{now()}"
  }}
}}
"""
        with tf_path.open("w") as f:
            f.write(tf)
        sh.run(("git", "add", tf_path))


class Slices(frozenset[Slice]):
    TOTAL = 3

    @classmethod
    def all(cls) -> Self:
        return cls(Slice(i) for i in range(cls.TOTAL))

    @classmethod
    def random(cls, seed: object = None, count: int | None = None) -> Self:
        random = Random(seed)
        if count is None:
            count = random.randint(1, cls.TOTAL)
            return cls.random(seed=seed, count=count)
        else:
            slices = random.sample(tuple(cls.all()), count)
            return cls(Slice(s) for s in slices)

    def assert_locked(self, xfail: XFails | None = None) -> None:
        for slice in range(self.TOTAL):
            slice = Slice(slice)
            locked = slice.is_locked()
            should_lock = slice in self

            try:
                assert locked == should_lock, (locked, slice)
            except AssertionError:
                if xfail is None:
                    raise

                # FIXME: actually do locking in our GHA "Obtain Lock" job
                assert locked == False
                xfail.append(
                    ("assert locked == False", (locked, should_lock, slice))
                )
