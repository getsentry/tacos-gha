#!/usr/bin/env py.test
from __future__ import annotations

from pathlib import Path

import hypothesis as H
from hypothesis import strategies as st

# actions/upload-artifact notes: Invalid characters include: ":<>|*?\r\n\/
INVALID_CHARACTERS = set("""":<>|*?\r\n\\/""")

interesting_text = st.lists(
    st.one_of(
        st.just("amp"),
        st.text(max_size=4, alphabet=("&", ";", "/", " ")),
        st.text(max_size=4, alphabet=sorted(INVALID_CHARACTERS)),
        st.just("&semi;"),
        st.text(max_size=4, alphabet=st.characters(max_codepoint=255)),
    ),
    max_size=4,
).map("".join)

HERE = Path(__file__).parent


@H.given(interesting_text, st.just(None))
@H.settings(max_examples=20)
@H.example("  ", "    ")
@H.example(" $$", "  $$$$")
@H.example("%  ", "%    ")
@H.example("; ", ";;  ")
@H.example("$/", "$$ ")
@H.example("a/b/c", "a b c")
@H.example("a b c", "a  b  c")
@H.example("a/ b /c", "a   b   c")
@H.example("& amp& ", None)
def test_encode_decode(before: str, intermediate: None | bytes):
    print(repr(before), end=" <-> ")
    from subprocess import check_output

    H.note(f"before : {before!r}")
    encoded = check_output(HERE / "ghaencode", input=before.encode("latin1"))
    print(repr(encoded))
    H.note(f"encoded: {encoded!r}")
    ## if intermediate is not None:
    ##     assert intermediate == encoded
    decoded = check_output(HERE / "ghadecode", input=encoded)
    decoded = decoded.decode("latin1")
    H.note(f"decoded: {decoded!r}")

    assert before == decoded

    assert not set(encoded.decode("latin1")) & INVALID_CHARACTERS
