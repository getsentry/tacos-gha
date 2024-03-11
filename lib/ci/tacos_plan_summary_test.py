#!/usr/bin/env py.test
from __future__ import annotations

from .tacos_plan_summary import Log
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
    )


def gen_error_slice(index: int, commands: int = 1) -> SliceSummary:
    return SliceSummary(
        f"error-slice-{index}",
        tf_log=(),
        console_log=gen_console_log(commands),
        tacos_verb="apply",
        explanation="",
        returncode=3 + index,
    )


def gen_clean_slice(index: int) -> SliceSummary:
    return SliceSummary(
        f"clean-slice-{index}",
        tf_log=("ohai", "wut"),
        console_log=("$ echo ok", "ok"),
        tacos_verb="clean",
        explanation="All's swell!",
        returncode=0,
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
                size_budget=2000,
            )
        )

        assert (
            result
            == """\
# Terraform Plan
TACOS generated a terraform plan for 3 slices:

  * 1 slices failed to plan
  * 1 slices have pending changes to apply
  * 1 slices are unaffected

## Errors

### error-slice-30 <!--🌮:apply-->

error code 33
Commands: (error code 33)

```console
$ echo $((2 ** 0))
1
```


## Changes

### dirty-slice-1 <!--🌮:plan-->
I'm dirty!

<details>
<summary>Plan: 100 to apply</summary>
<details>
<summary>Commands: (success, tfplan todo)</summary>

```console
$ echo $((2 ** 0))
1
```
</details>
  Result:

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
                size_budget=5_000,
            )
        )
        assert (
            result
            == """\
# Terraform Plan
TACOS generated a terraform plan for 1 slices:

  * 1 slices have pending changes to apply

## Changes

### dirty-slice-0 <!--🌮:plan-->
I'm dirty!

<details>
<summary>Plan: 100 to apply</summary>
<details>
<summary>Commands: (success, tfplan todo)</summary>

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
...
( 3.1KB, 164 lines skipped )
...
19807040628566084398385987584
$ echo $((2 ** 95))
39614081257132168796771975168
$ echo $((2 ** 96))
79228162514264337593543950336
$ echo $((2 ** 97))
158456325028528675187087900672
$ echo $((2 ** 98))
316912650057057350374175801344
$ echo $((2 ** 99))
633825300114114700748351602688
```
</details>
  Result:

```hcl
~ resource null_resource[0]
~   name = 0

~ resource null_resource[1]
~   name = 1

~ resource null_resource[2]
~   name = 2

...
( 45.5KB, 2981 lines skipped )
...

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
        size_budget = 64000
        n = 500
        slices = (
            [gen_error_slice(i) for i in range(n)]
            + [gen_dirty_slice(i) for i in range(n)]
            + [gen_clean_slice(i) for i in range(n)]
        )

        result = "\n".join(tacos_plan_summary(slices, size_budget=size_budget))

        assert size_budget * 0.8 < len(result) < size_budget

        for slice in slices:
            assert slice.tag in result

    def it_truncates_too_many_slices(self) -> None:
        size_budget = 1000
        n = 20
        slices = (
            [gen_error_slice(i) for i in range(n + 1)]
            + [gen_dirty_slice(i) for i in range(n + 2)]
            + [gen_clean_slice(i) for i in range(n + 3)]
        )

        result = "\n".join(tacos_plan_summary(slices, size_budget=size_budget))

        assert size_budget * 0.75 < len(result) < size_budget
        assert (
            result
            == """\
# Terraform Plan
TACOS generated a terraform plan for 66 slices:

  * 21 slices failed to plan
  * 22 slices have pending changes to apply
  * 23 slices are unaffected

## Errors
### Further Errors
These slices' logs could not be shown due to size constraints.
 * error-slice-0 <!--🌮:apply-->
 * error-slice-1 <!--🌮:apply-->
 * error-slice-2 <!--🌮:apply-->
 * error-slice-3 <!--🌮:apply-->
 * error-slice-4 <!--🌮:apply-->
 * error-slice-5 <!--🌮:apply-->
 * (15 slices skipped due to size)

## Changes
### Further Changes
These slices' logs could not be shown due to size constraints.
 * dirty-slice-0 <!--🌮:plan-->
 * dirty-slice-1 <!--🌮:plan-->
 * dirty-slice-2 <!--🌮:plan-->
 * dirty-slice-3 <!--🌮:plan-->
 * dirty-slice-4 <!--🌮:plan-->
 * (17 slices skipped due to size)

## Clean
These slices are in scope of your PR, but Terraform
found no infra changes are currently necessary:
  * (23 slices skipped, due to comment size)"""
        )

        assert slices[0].tag in result

    def it_handles_long_footer(self) -> None:
        del self

    def it_shows_first_error_preferentially(self) -> None:
        del self
