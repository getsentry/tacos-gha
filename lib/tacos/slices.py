#!/usr/bin/env python3.12
from __future__ import annotations

from .dependent_slices import FileSystem
from .dependent_slices import TFCategorized


def main() -> int:
    fs = FileSystem.from_git()
    categorized = TFCategorized.from_fs(fs)
    for slice in sorted(categorized.slices):
        print(slice)

    return 0


if __name__ == "__main__":
    exit(main())
