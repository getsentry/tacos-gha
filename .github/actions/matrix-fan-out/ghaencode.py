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

# actions/upload-artifact notes: Invalid characters include: ":<>|*?\r\n\/
DOC = __doc__
INVALID_CHARACTERS = """":<>|*?\r\n\\/"""

SUBSTITUTE_CHAR: Mapping[str, str] = {
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
assert not set(INVALID_CHARACTERS) - set(SUBSTITUTE_CHAR)

REVERSE: Mapping[str, str] = {rhs: lhs for lhs, rhs in SUBSTITUTE_CHAR.items()}

ESCAPE = " "


def ghaencode(s: str) -> str:
    buf: list[str] = []

    for c in reversed(s):
        if c == ESCAPE or c in REVERSE:
            buf.extend((ESCAPE, c))
        elif (c2 := SUBSTITUTE_CHAR.get(c)) is not None:
            buf.append(c2)
        else:
            buf.append(c)

    return "".join(reversed(buf))


def unescape(
    char0: str, char1: str | None
) -> tuple[str, str | None, str | None]:
    if char0 == ESCAPE and char1 is not None:
        return char1, None, None

    elif (char2 := REVERSE.get(char0)) is not None:
        return char2, char1, None

    else:
        return char0, char1, None


def ghadecode(s: str) -> str:
    buf: list[str] = []
    chars = iter(reversed(s))
    del s  # use chars

    char0 = char1 = None
    for char0 in chars:
        for char1 in chars:
            c, char0, char1 = unescape(char0, char1)
            buf.append(c)

            if char0 is None:
                break

    if char0 is not None:
        c, char0, char1 = unescape(char0, char1)
        buf.append(c)

    # we've exhausted our input:
    assert char0 is char1 is None, (char0, char1)

    return "".join(reversed(buf))
