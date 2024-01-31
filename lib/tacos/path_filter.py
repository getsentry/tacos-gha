#!/usr/bin/env python3.12
from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch

from lib.types import OSPath

DEFAULT_PATH = OSPath(".config/tacos-gha/slices.allowlist")


@dataclass(frozen=True)
class PathFilter:
    """A frozen view of a collection of files."""

    allowed: frozenset[str]

    def match(self, path: str) -> bool:
        if not self.allowed:
            return True
        for pattern in self.allowed:
            if fnmatch(str(path), pattern):
                return True
        return False

    @classmethod
    def from_config(cls, path: OSPath) -> PathFilter:
        """Get a list of allowed globs from a file

        Hash comments are removed and blank lines are ignored.
        Inline comments are not allowed
        If both the provided and default files are missing, allow all.
        Globs are evaluated with the fnmatch module."""
        lines: list[str] = []
        try:
            with path.open() as config:
                for line in config:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        lines.append(line)
        except FileNotFoundError:
            try:
                with DEFAULT_PATH.open() as config:
                    for line in config:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            lines.append(line)
            except FileNotFoundError:
                pass
        return cls(allowed=frozenset(lines))


def main() -> int:
    import fileinput

    path_filter = PathFilter.from_config(DEFAULT_PATH)

    for line in fileinput.input(encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if path_filter.match(line):
            print(line)

    return 0


if __name__ == "__main__":
    exit(main())
