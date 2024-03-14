#!/usr/bin/env py.test
from __future__ import annotations

from lib.byte_budget import ByteBudget
from lib.byte_budget import Log

from .tacos_plan_summary import SliceSummary
from .tacos_plan_summary import ensmallen
from .tacos_plan_summary import tacos_plan_summary


def gen_console_log(commands: int) -> Log:
    return tuple(
        line
        for i in range(commands)
        for line in (f"$ echo $((2 ** {i}))", str(2**i))
    )


def gen_dirty_slice(
    index: int, resources: int = 1000, commands: int = 100
) -> SliceSummary:
    return SliceSummary(
        f"dirty-slice-{index}",
        tf_log=tuple(
            line
            for i in range(resources)
            for line in (
                f"~ resource null_resource[{i}]",
                f"~   name = {i}",
                "",
            )
        )
        + ("Plan: 100 to apply",),
        console_log=gen_console_log(commands),
        tacos_verb="plan",
        explanation="I'm dirty" + "!" * int(index / 4 + 1),
        returncode=2,
        url="about:dirty",
    )


def gen_error_slice(index: int, commands: int = 1) -> SliceSummary:
    return SliceSummary(
        f"error-slice-{index}",
        tf_log=(),
        console_log=gen_console_log(commands),
        tacos_verb="apply",
        explanation="",
        returncode=3 + index,
        url=f"about:error#{index}",
    )


def gen_clean_slice(index: int) -> SliceSummary:
    return SliceSummary(
        f"clean-slice-{index}",
        tf_log=("ohai", "wut"),
        console_log=("$ echo ok", "ok"),
        tacos_verb="clean",
        explanation="All's swell!",
        returncode=0,
        url=f"slice://clean/{index}",
    )


class DescribeEnsmallen:
    def it_shows_small_input(self) -> None:
        lines = list(str(i) for i in range(10))
        result = ensmallen(lines=lines, size_limit=200)

        assert list(result) == lines

    def it_shows_input_at_exact_limit(self) -> None:
        lines = list(str(i) for i in range(10))
        result = ensmallen(lines=lines, size_limit=20)

        assert list(result) == lines

    def it_wont_lengthen_over_limit(self) -> None:
        lines = list(str(i) for i in range(11))
        result = ensmallen(lines=lines, size_limit=20)

        assert list(result) == lines

    def it_shortens_huge_input(self) -> None:
        lines = list(str(i) for i in range(1000))
        result = ensmallen(lines=lines, size_limit=30)

        assert list(result) == [
            "0",
            "1",
            "2",
            "3",
            "4",
            "...",
            "( 3.9KB, 993 lines skipped )",
            "...",
            "998",
            "999",
        ]

    def it_shortens_input_just_over_limit(self) -> None:
        lines = list(str(i) * 9 for i in range(9))
        length = 9 * 10  # nine lines of length ten

        # first show we don't shorten using exact length:
        result = ensmallen(lines=lines, size_limit=length)
        assert list(result) == lines

        result = ensmallen(lines=lines, size_limit=length - 1)

        assert list(result) == [
            "000000000",
            "111111111",
            "...",
            "( 0.0KB, 4 lines skipped )",
            "...",
            "666666666",
            "777777777",
            "888888888",
        ]

    def it_can_handle_huge_lines(self) -> None:
        lines = list(str(i) for i in range(10))
        lines[2] = lines[2] * 999
        lines[4] = lines[4] * 999
        result = ensmallen(lines=lines, size_limit=30)

        assert list(result) == [
            "0",
            "1",
            "...",
            "( 2.0KB, 3 lines skipped )",
            "...",
            "5",
            "6",
            "7",
            "8",
            "9",
        ]


class DescribeTacosPlanSummary:
    def it_shows_short_output_entirely(self) -> None:
        result = "\n".join(
            tacos_plan_summary(
                slices=[
                    gen_clean_slice(22),
                    gen_dirty_slice(1, resources=1, commands=1),
                    gen_error_slice(30),
                ],
                budget=ByteBudget(2000),
                run_id=2,
            )
        )

        assert (
            result
            == """\
# [Terraform Plan](https://github.com/getsentry/ops/actions/runs/2)
TACOS generated a terraform plan for 3 slices:

* 1 slices failed to plan
* 1 slices have pending changes to apply
* 1 slices are unaffected

## Errors

### [error-slice-30 <!--🌮:apply-->](about:error#30)

Failure: error code 33
Commands: (error code 33)

```console
$ echo $((2 ** 0))
1
```


## Changes

### [dirty-slice-1 <!--🌮:plan-->](about:dirty)
I'm dirty!

<details>
<summary>Plan: 100 to apply</summary>

```hcl
~ resource null_resource[0]
~   name = 0

Plan: 100 to apply
```
</details>


## Clean
These slices are in scope of your PR, but Terraform
found no infra changes are currently necessary:
* clean-slice-22 <!--🌮:clean-->"""
        )

    def it_shortens_long_output(self) -> None:
        result = "\n".join(
            tacos_plan_summary(
                slices=[gen_dirty_slice(0, resources=1000, commands=100)],
                budget=ByteBudget(5_000),
                run_id=8888,
            )
        )
        assert (
            result
            == """\
# [Terraform Plan](https://github.com/getsentry/ops/actions/runs/8888)
TACOS generated a terraform plan for 1 slices:

* 1 slices have pending changes to apply

## Changes

### [dirty-slice-0 <!--🌮:plan-->](about:dirty)
I'm dirty!

<details>
<summary>Plan: 100 to apply</summary>

```hcl
~ resource null_resource[0]
~   name = 0

~ resource null_resource[1]
~   name = 1

~ resource null_resource[2]
~   name = 2

~ resource null_resource[3]
~   name = 3

~ resource null_resource[4]
~   name = 4

~ resource null_resource[5]
~   name = 5

~ resource null_resource[6]
~   name = 6

~ resource null_resource[7]
~   name = 7

...
( 45.1KB, 2953 lines skipped )
...
~   name = 992

~ resource null_resource[993]
~   name = 993

~ resource null_resource[994]
~   name = 994

~ resource null_resource[995]
~   name = 995

~ resource null_resource[996]
~   name = 996

~ resource null_resource[997]
~   name = 997

~ resource null_resource[998]
~   name = 998

~ resource null_resource[999]
~   name = 999

Plan: 100 to apply
```
</details>
"""
        )

    def it_can_handle_a_huge_number_slices(self) -> None:
        """Show a large number of slices without any truncation."""
        budget = ByteBudget(64000)
        remainder = ByteBudget(budget)
        n = 600
        slices = (
            [gen_error_slice(i) for i in range(n)]
            + [gen_dirty_slice(i) for i in range(n)]
            + [gen_clean_slice(i) for i in range(n)]
        )

        result = "\n".join(
            tacos_plan_summary(slices, budget=remainder, run_id=111)
        )

        # assert (budget * 0.8) < len(result)
        assert len(result) < budget
        assert 0 <= remainder <= budget * 0.25

        for slice in slices:
            assert slice.tag in result

    def it_truncates_way_too_many_slices(self) -> None:
        budget = ByteBudget(1000)
        remainder = ByteBudget(budget)
        n = 999
        slices = (
            [gen_error_slice(i) for i in range(n + 1)]
            + [gen_dirty_slice(i) for i in range(n + 2)]
            + [gen_clean_slice(i) for i in range(n + 3)]
        )

        result = "\n".join(
            tacos_plan_summary(slices, budget=remainder, run_id=77)
        )

        # assert budget * 0.75 < len(result)
        assert len(result) < budget
        assert 0 <= remainder <= budget * 0.25

        assert (
            result
            == """\
# [Terraform Plan](https://github.com/getsentry/ops/actions/runs/77)
TACOS generated a terraform plan for 3003 slices:

* 1000 slices failed to plan
* 1001 slices have pending changes to apply
* 1002 slices are unaffected

## Errors
### Further Errors
These slices' logs could not be shown due to size constraints.
* error-slice-0 <!--🌮:apply-->
* error-slice-1 <!--🌮:apply-->
* error-slice-2 <!--🌮:apply-->
* error-slice-3 <!--🌮:apply-->
* error-slice-4 <!--🌮:apply-->
* (995 more slices not shown)

## Changes
### Further Changes
These slices' logs could not be shown due to size constraints.
* dirty-slice-0 <!--🌮:plan-->
* dirty-slice-1 <!--🌮:plan-->
* dirty-slice-2 <!--🌮:plan-->
* dirty-slice-3 <!--🌮:plan-->
* dirty-slice-4 <!--🌮:plan-->
* (996 more slices not shown)

## Clean
These slices are in scope of your PR, but Terraform
found no infra changes are currently necessary:
* clean-slice-0 <!--🌮:clean-->
* clean-slice-1 <!--🌮:clean-->
* (1000 more slices not shown)"""
        )

        assert slices[0].tag in result

    def it_shows_first_error_preferentially(self) -> None:
        budget = ByteBudget(1500)
        remainder = ByteBudget(budget)
        slices = [gen_error_slice(i, commands=20) for i in range(2)]

        # breakpoint()
        result = "\n".join(
            tacos_plan_summary(slices, budget=remainder, run_id=3)
        )

        # assert budget * 0.75 < len(result)
        assert len(result) < budget
        assert 0 <= remainder
        assert (
            result
            == """\
# [Terraform Plan](https://github.com/getsentry/ops/actions/runs/3)
TACOS generated a terraform plan for 2 slices:

* 2 slices failed to plan

## Errors

### [error-slice-0 <!--🌮:apply-->](about:error#0)

Failure: error code 3
Commands: (error code 3)

```console
$ echo $((2 ** 0))
1
$ echo $((2 ** 1))
2
$ echo $((2 ** 2))
4
$ echo $((2 ** 3))
8
$ echo $((2 ** 4))
16
$ echo $((2 ** 5))
32
...
( 0.2KB, 17 lines skipped )
...
16384
$ echo $((2 ** 15))
32768
$ echo $((2 ** 16))
65536
$ echo $((2 ** 17))
131072
$ echo $((2 ** 18))
262144
$ echo $((2 ** 19))
524288
```


### [error-slice-1 <!--🌮:apply-->](about:error#1)

<details>
<summary>Failure: error code 4</summary>
<details>
<summary>Commands: (error code 4)</summary>

```console
$ echo $((2 ** 0))
1
$ echo $((2 ** 1))
2
$ echo $((2 ** 2))
4
$ echo $((2 ** 3))
8
$ echo $((2 ** 4))
16
$ echo $((2 ** 5))
32
$ echo $((2 ** 6))
64
$ echo $((2 ** 7))
128
$ echo $((2 ** 8))
256
$ echo $((2 ** 9))
512
$ echo $((2 ** 10))
1024
$ echo $((2 ** 11))
2048
$ echo $((2 ** 12))
4096
$ echo $((2 ** 13))
8192
$ echo $((2 ** 14))
16384
$ echo $((2 ** 15))
32768
$ echo $((2 ** 16))
65536
$ echo $((2 ** 17))
131072
$ echo $((2 ** 18))
262144
$ echo $((2 ** 19))
524288
```
</details>
</details>
"""
        )
