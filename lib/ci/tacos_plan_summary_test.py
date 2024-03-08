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
        explanation="I'm dirty" + "!" * int(index / 2 + 1),
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
        f"a-very-nice-and-clean-slice-with-a-long-name-{index}",
        tf_log=("ohai", "wut"),
        console_log=("$ echo ok", "ok"),
        tacos_verb="xyz",
        explanation="All's swell!",
        returncode=0,
    )


class DescribeEnsmallen:
    def it_shows_small_input(self):
        lines = list(str(i) for i in range(10))
        result = ensmallen(lines=lines, size_limit=200)

        assert list(result) == lines

    def it_shows_input_at_exact_limit(self):
        lines = list(str(i) for i in range(10))
        result = ensmallen(lines=lines, size_limit=20)

        assert list(result) == lines

    def it_wont_lengthen_over_limit(self):
        lines = list(str(i) for i in range(11))
        result = ensmallen(lines=lines, size_limit=20)

        assert list(result) == lines

    def it_shortens_huge_input(self):
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

    def it_shortens_input_just_over_limit(self):
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

    def it_can_handle_huge_lines(self):
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
    def it_shows_short_output_entirely(self):
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

### error-slice
I want a sandwich!

  error code 33
<details>
  <summary>Commands: (error code 33)</summary>

```console
$ echo ok
ok
```
</details>
  Result:

```hcl
ohai
wut
```
<!-- getsentry/tacos-gha "apply(error-slice)" -->


## Changes

### dirty-slice
I want a sandwich!

<details>
  <summary>error code 2</summary>
<details>
  <summary>Commands: (error code 2)</summary>

```console
$ echo ok
ok
```
</details>
  Result:

```hcl
ohai
wut
```
</details>
<!-- getsentry/tacos-gha "apply(dirty-slice)" -->


## Clean
These slices are in scope of your PR, but Terraform
found no infra changes are currently necessary:
  * clean-slice
<!-- getsentry/tacos-gha "apply(clean-slice)" -->
"""
        )

    def it_shortens_long_output(self):
        result = "\n".join(
            tacos_plan_summary(
                slices=[
                    SliceSummary(
                        "dirty-slice",
                        tf_log=tuple(
                            line
                            for i in range(1000)
                            for line in (
                                f"~ resource null_resource[{i}]",
                                f"~   name = {i}",
                                "",
                            )
                        )
                        + ("Plan: 100 to apply",),
                        console_log=tuple(
                            line
                            for i in range(100)
                            for line in (f"$ echo $((2 ** {i}))", str(2**i))
                        ),
                        tacos_verb="plan",
                        explanation="I'm dirty.",
                        returncode=2,
                    )
                ],
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

### dirty-slice
I'm dirty.

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
...
( 3.2KB, 170 lines skipped )
...
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

~ resource null_resource[3]
~   name = 3

~ resource null_resource[4]
~   name = 4

~ resource null_resource[5]
...
( 45.3KB, 2970 lines skipped )
...
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
<!-- getsentry/tacos-gha "plan(dirty-slice)" -->
"""
        )

    def it_can_handle_way_too_many_slices(self):
        result = "\n".join(
            tacos_plan_summary(
                [gen_dirty_slice(i) for i in range(30)]
                + [gen_clean_slice(i) for i in range(30)]
                + [gen_error_slice(i) for i in range(30)],
                size_budget=5_000,
            )
        )
        assert result == ""

    def it_handles_long_footer(self):
        del self

    def it_shows_first_error_preferentially(self):
        del self
