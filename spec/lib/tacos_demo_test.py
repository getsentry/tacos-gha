#!/usr/bin/env py.test
from __future__ import annotations

from lib.types import Path
from spec.lib.slice import Slice

from .tacos_demo import parse_comment

COMMENT = """
# a/b/snarf <!--🌮:quux-->

abc a/z/ohai <!--🌮:fifi-->[ a/bebe <!--🌮:bobo-->](123)

* a/bar <!--🌮:foo-->

xyz
"""


class DescribeParseComment:
    def it_skips_irrelevant(self) -> None:
        assert (
            tuple(
                parse_comment(
                    job_filter=None, slices_subpath=Path(""), comment="oh, hi"
                )
            )
            == ()
        )

    def it_finds_comments(self) -> None:
        assert tuple(
            parse_comment(
                job_filter=None, slices_subpath=Path(""), comment=COMMENT
            )
        ) == (
            ("quux", Slice("a/b/snarf"), "\n# a/b/snarf <!--🌮:quux-->\n\n"),
            ("fifi", Slice("a/z/ohai"), "abc a/z/ohai <!--🌮:fifi-->"),
            ("bobo", Slice("a/bebe"), "[ a/bebe <!--🌮:bobo-->](123)\n\n"),
            ("foo", Slice("a/bar"), "* a/bar <!--🌮:foo-->\n\nxyz\n"),
        )

    def it_can_filter_job(self) -> None:
        assert tuple(
            parse_comment(
                job_filter="quux", slices_subpath=Path(""), comment=COMMENT
            )
        ) == (
            ("quux", Slice("a/b/snarf"), "\n# a/b/snarf <!--🌮:quux-->\n\n"),
        )

    def it_can_subpath(self) -> None:
        assert tuple(
            parse_comment(
                job_filter=None, slices_subpath=Path("a"), comment=COMMENT
            )
        ) == (
            ("quux", Slice("b/snarf"), "\n# a/b/snarf <!--🌮:quux-->\n\n"),
            ("fifi", Slice("z/ohai"), "abc a/z/ohai <!--🌮:fifi-->"),
            ("bobo", Slice("bebe"), "[ a/bebe <!--🌮:bobo-->](123)\n\n"),
            ("foo", Slice("bar"), "* a/bar <!--🌮:foo-->\n\nxyz\n"),
        )
