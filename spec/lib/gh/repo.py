"""Representations of git repositories, both remote and local."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass

from lib.parse import Parse
from lib.sh import sh
from lib.types import OSPath
from lib.types import Path

from .types import URL
from .types import Generator


@dataclass(frozen=True)
class RemoteRepo:
    """A remote git repository, with a specified subpath.

    As a context, clone and clean up afterward, yielding the LocalRepo.
    """

    url: URL
    subpath: Path = Path("")

    def __post_init__(self) -> None:
        assert not self.subpath.is_absolute(), self

    @contextmanager
    def cloned(self, dest: OSPath) -> Generator[LocalRepo]:
        repo = self.clone(dest)
        yield repo
        # cleanup makes debugging harder, plus pytest's tmp_path handles it
        # sh.run(("rm", "-rf", repo.path))

    @property
    def name(self) -> str:
        return Parse(self.url).after.last(":", "/")

    def clone(self, dest: OSPath) -> LocalRepo:
        dest = dest / self.name
        # git will fail if the repo already exists, and that's a feature
        sh.run((
            "git",
            "clone",
            "-q",  # suppress noisy progress reports
            # best for build environments where the repository will be
            # deleted after a single build
            "--filter=tree:0",
            "git@github.com:getsentry/tacos-gha.demo",
            dest,
        ))
        return LocalRepo(remote=self, path=dest)

    def __str__(self) -> str:
        return f"{self.url}//{self.subpath}"


@dataclass(frozen=True)
class LocalRepo:
    """A local checkout of some remote git repository."""

    remote: RemoteRepo
    path: OSPath

    def __str__(self) -> str:
        return str(self.path)

    @property
    def workdir(self) -> OSPath:
        return self.path / self.remote.subpath
