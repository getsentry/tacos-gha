#!/usr/bin/env python3
from __future__ import annotations

import os
from typing import Set

from lib.types import OSPath


def gather_unique_paths(path: OSPath) -> Set[str]:
    """
    Gathers all unique paths (slices) referenced in the matrix.list file.
    Each line in matrix.list is a slice that is plan will run on.
    """
    unique_paths: set[str] = set()
    matrix_list_path = path / "matrix.list"
    with matrix_list_path.open() as matrix_file:
        for line in matrix_file:
            matrix_path = line.strip()
            unique_paths.add(matrix_path)

    return unique_paths


def get_slices() -> int:
    try:
        arg = os.getenv("MATRIX_FAN_OUT_PATH", "./matrix-fan-out")
        path = OSPath(arg)
        unique_paths = gather_unique_paths(path)
        print(",".join(unique_paths))
    except Exception as e:
        print(f"Error gathering slices: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(get_slices())
