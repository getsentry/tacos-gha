#!/usr/bin/env py.test
from __future__ import annotations

from pathlib import Path

from lib.sh import sh

from . import slice


class DescribeSlice:
    def it_knows_its_directory(self, tmp_path: Path) -> None:
        with sh.cd(tmp_path, direnv=False):
            relpath = "slice-99ohai"
            slice_path = tmp_path / relpath
            slice_path.mkdir()

            slice99 = slice.Slice(relpath)
            assert slice99.samefile(slice_path)
