#!/usr/bin/env python3
from __future__ import annotations

import os
from typing import Set

from lib.types import OSPath


def gather_unique_paths(path: OSPath) -> Set[str]:
    """
    Gathers all unique paths (slices) referenced in the matrix.list file.
    Each line in matrix.list points to a directory or file to be processed.
    """
    unique_paths: set[str] = set()
    matrix_list_path = path / "matrix.list"

    try:
        with matrix_list_path.open() as matrix_file:
            for line in matrix_file:
                matrix_path = line.strip()
                # Assuming each matrix path is unique, or process as needed
                unique_paths.add(matrix_path)
    except FileNotFoundError:
        print(f"Error: {matrix_list_path} not found.")

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
