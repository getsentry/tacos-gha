#!/usr/bin/env python3
# a silly script to print the "square" of a number:
#
# $ square.py 4
# 1 2 3 4
# 2 4 4 4
# 3 4 4 4
# 4 4 4 4

from __future__ import annotations

from sys import argv

arg = argv[1]
n = int(arg)


def indent(o: object) -> str:
    return str(o).rjust(len(arg))


for row in range(1, n + 1):
    if row == 1:
        print(" ".join(indent(col) for col in range(1, n + 1)))
    else:
        vals = [indent(row)] + [arg] * (n - 1)
        print(" ".join(vals))
