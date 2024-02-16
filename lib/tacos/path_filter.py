#!/usr/bin/env python3.12
from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch

from lib.sh import sh
from lib.types import OSPath

DEFAULT_PATH = ".config/tacos-gha/slices.allowlist"


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
    def from_config(cls, config: str) -> PathFilter:
        """Get a list of allowed globs from a file

        Hash comments are removed and blank lines are ignored.
        Inline comments are not allowed
        If both the provided and default files are missing, allow all.
        Globs are evaluated with the fnmatch module."""
        lines: list[str] = []
        for path in OSPath(config), OSPath(DEFAULT_PATH):
            try:
                with path.open() as config_file:
                    sh.info(
                        f"TACOS-gha: Using slice-allowlist from path: {path}"
                    )
                    for line in config_file:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            lines.append(line)
                break
            except FileNotFoundError:
                continue
        else:
            sh.info(
                f"TACOS-gha: allowing all slices due to lack of config: {config}"
            )
        return cls(allowed=frozenset(lines))


def main() -> int:
    import fileinput
    from sys import argv

    args = argv[1:]
    # need to modify argv for fileinput to work
    del argv[1:]

    path_filter = PathFilter.from_config(*args)

    for line in fileinput.input(encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if path_filter.match(line):
            print(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
