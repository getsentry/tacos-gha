#!/usr/bin/env python3.12
from __future__ import annotations

import re
import typing
from dataclasses import dataclass
from typing import Callable
from typing import Iterable
from typing import NewType
from typing import Self

from lib.types import OSPath
from lib.types import Path

# NewTypes exist only during typing, but help keep track of things
Dir = NewType("Dir", Path)
TFConfigDir = NewType("TFConfigDir", Dir)
File = NewType("File", Path)
TFConfigFile = NewType("TFConfigFile", File)
TFSharedModulesDir = NewType("TFSharedModulesDir", Dir)
TFModule = NewType("TFModule", Dir)
TopLevelTFModule = NewType("TopLevelTFModule", TFModule)  # AKA "slice"
SharedTFModule = NewType("SharedTFModule", TFModule)

T = typing.TypeVar("T")
P = typing.ParamSpec("P")
Generator = typing.Generator[T, None, None]
SliceDeps = dict[Dir, frozenset[TopLevelTFModule]]

TF_SUFFIX = ".tf"
TG_SUFFIX = ".hcl"
TF_SHARED_DIRNAME = frozenset({"module", "modules"})


def parent(path: Path) -> Dir:
    return Dir(path.parent)


@dataclass(frozen=True)
class FileSystem:
    """A frozen view of a collection of files."""

    files: frozenset[File]
    # only directories that (directly) contain files are included
    dirs: frozenset[Dir]

    @classmethod
    def from_paths(cls, paths: Iterable[OSPath]) -> Self:
        """Nonexistent paths are presumed to be files' paths."""
        files: set[File] = set()
        dirs: set[Dir] = set()

        for path in paths:
            if path.is_dir():
                dirs.add(Dir(Path(path)))
            else:
                file = File(Path(path))
                files.add(file)
                dirs.add(parent(file))

        return cls(files=frozenset(files), dirs=frozenset(dirs))

    @classmethod
    def from_git(cls, cwd: Dir | None = None) -> Self:
        if cwd is None:
            cwd = Dir(OSPath.cwd())

        from subprocess import run

        git_ls_files = run(
            ("git", "-C", str(cwd), "ls-files"),
            capture_output=True,
            check=True,
            encoding="US-ASCII",
        )
        paths = (
            OSPath(line.strip()) for line in git_ls_files.stdout.splitlines()
        )
        return cls.from_paths(paths)

    def ls_files(self, dir: Dir) -> Iterable[File]:
        for file in self.files:
            if parent(file) == dir:
                yield file


@dataclass(frozen=True)
class PathFilter:
    """A frozen view of a collection of files."""

    allowed: frozenset[re.Pattern[str]]

    def match(self, path: str) -> bool:
        for pattern in self.allowed:
            # intentionally uses match to check from the start of the string
            if pattern.match(path) is not None:
                return True
        return False

    @classmethod
    def from_config(cls, path: OSPath) -> PathFilter:
        """Get a list of allowed RE patterns from a file.

        # comments are removed and blank lines are ignored.
        An empty or missing file is treated as all allowed."""
        lines: list[re.Pattern[str]] = []
        # remove from the first unescaped # to the end
        comment_pattern = re.compile(r"(?<!\\)#.*")
        try:
            with path.open() as config:
                for line in config:
                    line = comment_pattern.sub("", line).strip()
                    if line:
                        lines.append(re.compile(line))
        except FileNotFoundError:
            lines.append(re.compile(""))
        if not lines:
            lines.append(re.compile(""))
        return cls(allowed=frozenset(lines))


@typing.overload
def paths_containing(path: Dir) -> Generator[Dir]:
    ...


@typing.overload
def paths_containing(path: File) -> Generator[Path]:
    ...


def paths_containing(path: Path) -> Generator[Path]:
    """inclusive"""
    yield path
    yield from path.parents


def dir_contains(dir: Dir, path: Path) -> bool:
    """ancestor, inclusive"""
    return dir == path or dir in path.parents


def tf_find_shared_dir(module: TFModule) -> TFSharedModulesDir | None:
    for parent in paths_containing(module):
        if parent.name in TF_SHARED_DIRNAME:
            return TFSharedModulesDir(parent)
    else:
        return None


def is_tf_module(dir: Dir, fs: FileSystem) -> TFModule | None:
    for file in fs.ls_files(dir):
        if file.suffix == TF_SUFFIX or file.name == "terragrunt.hcl":
            return TFModule(dir)
    else:
        return None


def is_tf_config(file: File) -> TFConfigFile | None:
    if file.suffix in (".tfvars", ".tf", ".hcl") or file.name.endswith(
        ".tf.json"
    ):
        return TFConfigFile(file)
    else:
        return None


@dataclass(frozen=True)
class TFCategorized:
    slices: frozenset[TopLevelTFModule]
    shared_dirs: frozenset[TFSharedModulesDir]
    config_files: frozenset[TFConfigFile]

    @classmethod
    def from_fs(
        cls, subject: FileSystem, fs: FileSystem | None = None
    ) -> Self:
        if fs is None:
            fs = subject

        slices: set[TopLevelTFModule] = set()
        shared_dirs: set[TFSharedModulesDir] = set()
        config_files: set[TFConfigFile] = set()

        for dir in subject.dirs:
            if module := is_tf_module(dir, fs):
                if shared_dir := tf_find_shared_dir(module):
                    shared_dirs.add(shared_dir)
                else:
                    slices.add(TopLevelTFModule(module))

        for file in subject.files:
            if config := is_tf_config(file):
                # we already track slices
                if any(parent(config) == slice for slice in slices):
                    continue
                # we already track shared dirs
                if any(
                    dir_contains(shared_dir, config)
                    for shared_dir in shared_dirs
                ):
                    continue
                config_files.add(config)

        return cls(
            frozenset(slices), frozenset(shared_dirs), frozenset(config_files)
        )

    @classmethod
    def from_modified_files(
        cls, modified_paths: Iterable[OSPath], fs: FileSystem
    ) -> Self:
        modified_fs = FileSystem.from_paths(modified_paths)
        return cls.from_fs(modified_fs, fs)

    def config_deps(self) -> SliceDeps:
        """Map from config dirs to the slices that (could) depend on them."""
        config_deps: dict[TFConfigDir, set[TopLevelTFModule]] = {}
        for config_dir in self.config_dirs:
            config_deps[config_dir] = set()
            for slice in self.slices:
                if dir_contains(config_dir, slice):
                    config_deps[config_dir].add(slice)

        return {var: frozenset(val) for var, val in config_deps.items()}

    @property
    def config_dirs(self) -> frozenset[TFConfigDir]:
        """directories containing a config file or a shared-modules dir"""
        return frozenset(
            TFConfigDir(parent(path))
            for paths in (self.shared_dirs, self.config_files)
            for path in paths
        )


def uniq(f: Callable[P, Iterable[T]]) -> Callable[P, Generator[T]]:
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> Generator[T]:
        seen: set[T] = set()
        for x in f(*args, **kwargs):
            if x in seen:
                continue
            else:
                yield x
                seen.add(x)

    return wrapped


@uniq
def dependent_slices(
    modified_paths: Iterable[OSPath], fs: FileSystem
) -> Generator[TopLevelTFModule]:
    """Which slices need to be planned?"""
    modified = TFCategorized.from_modified_files(modified_paths, fs)

    yield from sorted(modified.slices)

    # do we need to worry about indirect modifications?
    if modified.shared_dirs or modified.config_files:
        all = TFCategorized.from_fs(fs)
        config_deps = all.config_deps()
        for config_dir in modified.config_dirs:
            yield from sorted(config_deps[config_dir])


def lines_to_paths(lines: Iterable[str]) -> Generator[OSPath]:
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        yield OSPath(line)


def main() -> int:
    import fileinput

    fs = FileSystem.from_git()
    modified_paths = lines_to_paths(fileinput.input(encoding="utf-8"))

    path_filter = PathFilter.from_config(
        # TODO: does this path work in the calling repository?
        OSPath(".config/tacos-gha/slices.allowlist")
    )

    for slice in dependent_slices(modified_paths, fs):
        # TODO: calling str here is a little bit meh.
        if path_filter.match(str(slice)):
            print(slice)

    return 0


if __name__ == "__main__":
    exit(main())
