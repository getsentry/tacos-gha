#!/usr/bin/env -S python3.12 -P
from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch

from lib.types import OSPath

SLICE_ALLOW_CONFIG_PATH = OSPath(".config/tacos-gha/slices.allowlist")
SLICE_BLOCK_CONFIG_PATH = OSPath(".config/tacos-gha/slices.blocklist")
FILE_ALLOW_CONFIG_PATH = OSPath(".config/tacos-gha/files.allowlist")
FILE_BLOCK_CONFIG_PATH = OSPath(".config/tacos-gha/files.blocklist")


@dataclass(frozen=True)
class PathFilter:
    """A frozen view of a collection of files."""

    allowed: frozenset[str]
    blocked: frozenset[str]

    def match(self, path: str) -> bool:
        for pattern in self.blocked:
            if fnmatch(str(path), pattern):
                return False
        if not self.allowed:
            return True
        for pattern in self.allowed:
            if fnmatch(str(path), pattern):
                return True
        return False

    @classmethod
    def from_config(cls, allow_path: OSPath, block_path: OSPath) -> PathFilter:
        """Get a list of allowed and blocked globs from the config files

        Hash comments are removed and blank lines are ignored.
        Inline comments are not allowed
        An empty or missing allowlist file allows anything.
        An empty or missing blocklist file blocks nothing.
        Blocks take precedence over allows.
        Globs are evaluated with the fnmatch module."""
        allow_lines: list[str] = []
        # remove from the first unescaped # to the end
        try:
            with allow_path.open() as allow_config:
                for line in allow_config:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        allow_lines.append(line)
        except FileNotFoundError:
            pass
        block_lines: list[str] = []
        # remove from the first unescaped # to the end
        try:
            with block_path.open() as block_config:
                for line in block_config:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        block_lines.append(line)
        except FileNotFoundError:
            pass
        return cls(
            allowed=frozenset(allow_lines), blocked=frozenset(block_lines)
        )

    @classmethod
    def from_slices(cls) -> PathFilter:
        return cls.from_config(
            SLICE_ALLOW_CONFIG_PATH, SLICE_BLOCK_CONFIG_PATH
        )

    @classmethod
    def from_files(cls) -> PathFilter:
        return cls.from_config(FILE_ALLOW_CONFIG_PATH, FILE_BLOCK_CONFIG_PATH)


def main() -> int:
    import fileinput

    path_filter = PathFilter.from_slices()

    for line in fileinput.input(encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if path_filter.match(line):
            print(line)

    return 0


if __name__ == "__main__":
    exit(main())
