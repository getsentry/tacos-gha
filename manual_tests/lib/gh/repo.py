"""Representations of git repositories, both remote and local."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass

from lib.parse import after
from lib.sh import sh
from lib.types import OSPath
from lib.types import Path

from .types import URL
from .types import Generator


@dataclass(frozen=True)
class Remote:
    """A remote git repository, with a specified subpath.

    As a context, clone and clean up afterward, yielding the Local repo.
    """

    url: URL
    subpath: Path = Path("")

    def __post_init__(self) -> None:
        assert not self.subpath.is_absolute(), self

    @contextmanager
    def cloned(self, dest: OSPath) -> Generator[Local]:
        repo = self.clone(dest)
        yield repo
        # cleanup makes debugging harder, plus pytest's tmp_path handles it
        # sh.run(("rm", "-rf", repo.path))

    @property
    def name(self) -> str:
        return after(self.url, ":", "/")

    def clone(self, dest: OSPath) -> Local:
        dest = dest / self.name
        # git will fail if the repo already exists, and that's a feature
        sh.run(("git", "clone", "git@github.com:getsentry/tacos-demo", dest))
        return Local(remote=self, path=dest)

    def __str__(self) -> str:
        return f"{self.url}//{self.subpath}"


@dataclass(frozen=True)
class Local:
    """A local checkout of some remote git repository."""

    remote: Remote
    path: OSPath

    def __str__(self) -> str:
        return str(self.path)

    @property
    def workdir(self) -> OSPath:
        return self.path / self.remote.subpath
