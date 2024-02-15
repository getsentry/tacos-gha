#!/usr/bin/env py.test
from __future__ import annotations

from lib.types import Path
from spec.lib.slice import Slice

from .tacos_demo import parse_comment

COMMENT = """
abc
<!-- getsentry/tacos-gha "foo(a/bar)" -->
xyz
<!-- getsentry/tacos-gha "quux(a/b/snarf)" -->
123
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
            (
                "foo",
                Slice("a/bar"),
                '\nabc\n<!-- getsentry/tacos-gha "foo(a/bar)" -->',
            ),
            (
                "quux",
                Slice("a/b/snarf"),
                '\nxyz\n<!-- getsentry/tacos-gha "quux(a/b/snarf)" -->',
            ),
        )

    def it_can_filter_job(self) -> None:
        assert tuple(
            parse_comment(
                job_filter="quux", slices_subpath=Path(""), comment=COMMENT
            )
        ) == (
            (
                "quux",
                Slice("a/b/snarf"),
                '\nxyz\n<!-- getsentry/tacos-gha "quux(a/b/snarf)" -->',
            ),
        )

    def it_can_subpath(self) -> None:
        assert tuple(
            parse_comment(
                job_filter=None, slices_subpath=Path("a"), comment=COMMENT
            )
        ) == (
            (
                "foo",
                Slice("bar"),
                '\nabc\n<!-- getsentry/tacos-gha "foo(a/bar)" -->',
            ),
            (
                "quux",
                Slice("b/snarf"),
                '\nxyz\n<!-- getsentry/tacos-gha "quux(a/b/snarf)" -->',
            ),
        )
