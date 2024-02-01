#!/usr/bin/env py.test
from __future__ import annotations

from lib.sh import sh
from lib.types import OSPath

from . import slice


class DescribeSlice:
    def it_knows_its_directory(self, tmp_path: OSPath) -> None:
        with sh.cd(tmp_path, direnv=False):
            relpath = "slice-99ohai"
            slice_path = tmp_path / relpath
            slice_path.mkdir()

            slice99 = slice.Slice(relpath)
            assert slice_path.samefile(slice99)
