#!/usr/bin/env -S python3.12 -P
from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch

from lib.types import OSPath
from lib.types import Path

CONFIG_PATH = OSPath(".config/tacos-gha/slices.allowlist")
DISABLED_SENTINEL = ".tacos-disabled"


@dataclass(frozen=True)
class PathFilter:
    """A frozen view of a collection of files."""

    allowed: frozenset[str]
    disabled_sentinel: str = DISABLED_SENTINEL

    def is_disabled(self, path: str, fs_files: frozenset[Path] | None = None) -> bool:
        """Check if a slice is disabled by a sentinel file in it or any ancestor."""
        if fs_files is not None:
            return self._is_disabled_from_fs(path, fs_files)
        return self._is_disabled_from_disk(path)

    def _is_disabled_from_disk(self, path: str) -> bool:
        p = OSPath(path)
        for ancestor in (p, *p.parents):
            if (ancestor / self.disabled_sentinel).is_file():
                return True
        return False

    def _is_disabled_from_fs(self, path: str, fs_files: frozenset[Path]) -> bool:
        p = Path(path)
        for ancestor in (p, *p.parents):
            if Path(str(ancestor / self.disabled_sentinel)) in fs_files:
                return True
        return False

    def disabled_message(self, path: str) -> str:
        """Read the content of the nearest .tacos-disabled sentinel file."""
        p = OSPath(path)
        for ancestor in (p, *p.parents):
            sentinel = ancestor / self.disabled_sentinel
            if sentinel.is_file():
                content = sentinel.read_text().strip()
                if content:
                    return content
                break
        return "This slice has been disabled in TACOS-GHA."

    def match(self, path: str) -> bool:
        if not self.allowed:
            return True
        for pattern in self.allowed:
            if fnmatch(str(path), pattern):
                return True
        return False

    @classmethod
    def from_config(cls, path: OSPath = CONFIG_PATH) -> PathFilter:
        """Get a list of allowed globs from a file

        Hash comments are removed and blank lines are ignored.
        Inline comments are not allowed
        An empty or missing file is treated as all allowed.
        Globs are evaluated with the fnmatch module."""
        lines: list[str] = []
        # remove from the first unescaped # to the end
        try:
            with path.open() as config:
                for line in config:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        lines.append(line)
        except FileNotFoundError:
            pass
        return cls(allowed=frozenset(lines))


def main() -> int:
    import fileinput

    from lib.sh import sh

    path_filter = PathFilter.from_config()

    for line in fileinput.input(encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if path_filter.is_disabled(line):
            sh.debug(f"slice disabled by {DISABLED_SENTINEL}: {line}")
        elif path_filter.match(line):
            print(line)

    return 0


if __name__ == "__main__":
    exit(main())
