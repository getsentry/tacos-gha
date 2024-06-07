"""
Allow for arbitrary characters to be passed through gha artifact names, via
an escaping scheme. This means we can use user inputs as part of our artifact
names while still writing no code whatsoever to handle weird user inputs that
break the system.

All disallowed characters are replaced with lookalike unicode characters. If
those characters show up in the input (unlikely), " " is used as an
escape-suffix. A literal " " is doubled to escape it.

reference:
  actions/upload-artifact notes: Invalid characters include: ":<>|*?\r\n\\/
  in other words, valid characters include: ' `~!@#$%^&()_+{}-=[];,.
  unused escapes: ~@#`'()-=[]
"""

from __future__ import annotations

from typing import Mapping
from typing import assert_type

# actions/upload-artifact notes: Invalid characters include: ":<>|*?\r\n\/
DOC = __doc__
INVALID_CHARACTERS = """\":<>|*?\r\n\\/"""

ESCAPE_CHAR: str = " "
ESCAPE: Mapping[str, str] = {
    '"': "“",
    ":": "∶",  # ։
    "<": "‹",
    ">": "›",
    "|": "❘",  # ❘⎟⎥┃
    "*": "⋆",  # ⁕
    "?": "‽",  # ⸮
    "\r": "␍",
    "\n": "␊",
    "\\": "⧵",  # ⧹
    "/": "⧸",
}
assert not set(INVALID_CHARACTERS) - set(ESCAPE)

UNESCAPE: Mapping[str, str] = {rhs: lhs for lhs, rhs in ESCAPE.items()}


def ghaencode(s: str) -> str:
    buf: list[str] = []

    for c in reversed(s):
        if c == ESCAPE_CHAR or c in UNESCAPE:
            buf.extend((ESCAPE_CHAR, c))
        elif (c2 := ESCAPE.get(c)) is not None:
            buf.append(c2)
        else:
            buf.append(c)

    return "".join(reversed(buf))


def unescape(first: str, second: str | None) -> tuple[str, str | None, None]:
    if first == ESCAPE_CHAR and second is not None:
        return second, None, None

    elif (unescaped := UNESCAPE.get(first)) is not None:
        return unescaped, second, None

    else:
        return first, second, None


def ghadecode(s: str) -> str:
    buf: list[str] = []
    chars = iter(reversed(s))
    del s  # use chars

    first = second = None
    for first in chars:
        for second in chars:
            unescaped, first, second = unescape(first, second)
            buf.append(unescaped)

            if first is None:
                break
        else:
            assert_type(second, None)
            buf.append(UNESCAPE.get(first, first))
            first = None

    # proof: we've exhausted our input
    assert_type(first, None)
    assert_type(second, None)

    return "".join(reversed(buf))
