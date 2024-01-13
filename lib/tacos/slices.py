#!/usr/bin/env python3.12
from __future__ import annotations

from .dependent_slices import TFCategorized


def main() -> int:
    for slice in sorted(TFCategorized.from_git().slices):
        print(slice)

    return 0


if __name__ == "__main__":
    exit(main())
