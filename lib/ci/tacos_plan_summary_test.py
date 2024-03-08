#!/usr/bin/env py.test
from __future__ import annotations

from .tacos_plan_summary import ensmallen


class DescribeEnsmallen:
    def it_shows_small_input(self):
        lines = list(str(i) for i in range(10))
        result = ensmallen(lines=lines, limit=200)

        assert list(result) == lines

    def it_shows_input_at_exact_limit(self):
        lines = list(str(i) for i in range(10))
        result = ensmallen(lines=lines, limit=20)

        assert list(result) == lines

    def it_shortens_huge_input(self):
        lines = list(str(i) for i in range(1000))
        result = ensmallen(lines=lines, limit=30)

        assert list(result) == [
            "0",
            "1",
            "2",
            "3",
            "4",
            "...",
            "( 3KB, 993 lines skipped )",
            "...",
            "998",
            "999",
        ]

    def it_shortens_input_just_over_limit(self):
        lines = list(str(i) for i in range(11))
        result = ensmallen(lines=lines, limit=20)

        assert list(result) == [
            "0",
            "1",
            "2",
            "...",
            "( 0KB, 5 lines skipped )",
            "...",
            "8",
            "9",
            "10",
        ]

    def it_can_handle_huge_lines(self):
        lines = list(str(i) for i in range(10))
        lines[2] = lines[2] * 999
        lines[4] = lines[4] * 999
        result = ensmallen(lines=lines, limit=30)

        assert list(result) == [
            "0",
            "1",
            "...",
            "( 1KB, 3 lines skipped )",
            "...",
            "5",
            "6",
            "7",
            "8",
            "9",
        ]
