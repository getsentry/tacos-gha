from __future__ import annotations

import contextlib

from lib.constants import TACOS_GHA_HOME
from lib.sh import sh
from lib.types import Generator

# use util-linux's flock(1) to synchronize changes in github
GITHUB_FLOCK = TACOS_GHA_HOME / ".github.lock"


@contextlib.contextmanager
def up_to_date() -> Generator[None]:
    """Prevent errors in the face of parallel read/edit/writes to github."""
    with GITHUB_FLOCK.open("w") as flock:
        fd = flock.fileno()

        import os

        os.set_inheritable(fd, True)

        sh.run(("flock", fd))  # this may take time
        sh.run(("git", "status"))
        # rebase=false means "merge" /shrug
        sh.run(("git", "pull", "--rebase=false", "origin", "main"))
        yield
