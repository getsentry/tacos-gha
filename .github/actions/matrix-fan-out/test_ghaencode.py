#!/usr/bin/env py.test
from __future__ import annotations

from pathlib import Path

import hypothesis as H
from hypothesis import strategies as st

interesting_text = st.lists(
    st.one_of(st.sampled_from(("a", "/", " ", "_", "*", "  ", "$", ";", "&"))),
    max_size=4,
).map("".join)

HERE = Path(__file__).parent


@H.settings(max_examples=400)
@H.given(interesting_text, st.just(None))
@H.example("  ", "    ")
@H.example(" $$", "  $$$$")
@H.example("%  ", "%    ")
@H.example("; ", ";;  ")
@H.example("$/", "$$ ")
@H.example("a/b/c", "a b c")
@H.example("a b c", "a  b  c")
@H.example("a/ b /c", "a   b   c")
def test_encode_decode(before: str, intermediate: None | bytes):
    print(repr(before))
    from subprocess import check_output

    H.note(f"before : {before!r}")
    encoded = check_output(HERE / "ghaencode", input=before, encoding="latin1")
    print("   ", repr(encoded))
    H.note(f"encoded: {encoded!r}")
    ## if intermediate is not None:
    ##     assert intermediate == encoded
    decoded = check_output(HERE / "ghadecode", input=encoded.encode("latin1"))
    decoded = decoded.decode("latin1")
    H.note(f"decoded: {decoded!r}")

    assert before == decoded
