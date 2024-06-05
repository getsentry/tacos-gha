#!/usr/bin/env py.test
from __future__ import annotations

from pathlib import Path

import hypothesis as H
from ghaencode import ESCAPE
from ghaencode import SUBSTITUTE_CHAR
from ghaencode import ghadecode
from ghaencode import ghaencode
from hypothesis import strategies as st

# actions/upload-artifact notes: Invalid characters include: ":<>|*?\r\n\/
INVALID_CHARACTERS = """":<>|*?\r\n\\/"""


@st.composite
def interesting_text(draw: st.DrawFn) -> str:
    s = "".join(
        draw(
            st.lists(
                st.one_of(
                    st.just("foo"),
                    st.just(ESCAPE),
                    st.sampled_from(tuple(SUBSTITUTE_CHAR.values())),
                    st.sampled_from(tuple(SUBSTITUTE_CHAR)),
                    st.text(max_size=4),
                ),
                max_size=4,
            )
        )
    )

    i = draw(st.integers(0, 2))
    if i == 0:
        return s
    elif i == 1:
        return ghaencode(s)
    elif i == 2:
        return ghadecode(s)
    else:
        raise AssertionError(i)


HERE = Path(__file__).parent


@H.given(interesting_text())
@H.settings(max_examples=1000, verbosity=H.Verbosity.verbose)
@H.example("։ ")
@H.example("a/ b /c")
@H.example("& amp& ")
@H.example(" ։")
def test_encode_decode(before: str):
    H.note(f"before : {before!r}")
    encoded = ghaencode(before)

    H.note(f"encoded: {encoded!r}")
    decoded = ghadecode(encoded)

    H.note(f"decoded: {decoded!r}")
    assert before == decoded

    # encoded string must have no 'invalid characters'
    assert not set(encoded) & set(INVALID_CHARACTERS)
