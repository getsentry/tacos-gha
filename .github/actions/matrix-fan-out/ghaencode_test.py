#!/usr/bin/env py.test
from __future__ import annotations

from pathlib import Path

import hypothesis as H
from ghaencode import ESCAPE
from ghaencode import ESCAPE_CHAR
from ghaencode import INVALID_CHARACTERS
from ghaencode import ghadecode
from ghaencode import ghaencode
from hypothesis import strategies as st


@st.composite
def interesting_text(draw: st.DrawFn) -> str:
    result: str = draw(
        st.text(
            alphabet=st.one_of(
                st.just("x"),
                st.sampled_from(INVALID_CHARACTERS),
                st.just(ESCAPE_CHAR),
                st.sampled_from(sorted(ESCAPE)),
                st.characters(),
            ),
            max_size=7,
        )
    )

    i = draw(st.integers(0, 2))
    if i == 0:
        return result
    elif i == 1:
        return ghaencode(result)
    elif i == 2:
        return ghadecode(result)
    else:
        raise AssertionError(i)


HERE = Path(__file__).parent


@H.given(interesting_text())
@H.settings(
    max_examples=2**8,  # 2**13 for a ~10s thorough search
    report_multiple_bugs=False,
    verbosity=H.Verbosity.verbose,
    deadline=1,  # milliseconds
)
@H.example("xyz")
@H.example("a/b/c")
@H.example(" a/ b /c ")
@H.example("։ ")
@H.example("“")
def test_encode_decode(before: str):
    encoded = ghaencode(before)

    H.note(f"encoded: {encoded!r}")
    decoded = ghadecode(encoded)

    assert before == decoded

    # encoded string must have no 'invalid characters'
    assert not set(encoded) & set(INVALID_CHARACTERS)
