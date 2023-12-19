from __future__ import annotations

#   head   ---x    x
#   tail      x----x---
#   before ---x----x
#   after     x    x---


def head(s: str, *separators: str) -> str:
    for sep in separators:
        s = s.split(sep, 1)[0]
    return s


def tail(s: str, *separators: str) -> str:
    for sep in separators:
        s = s.split(sep, 1)[-1]
    return s


def before(s: str, *separators: str) -> str:
    for sep in separators:
        s = s.rsplit(sep, 1)[0]
    return s


def after(s: str, *separators: str) -> str:
    for sep in separators:
        s = s.rsplit(sep, 1)[-1]
    return s
