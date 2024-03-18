#!/usr/bin/env py.test
from __future__ import annotations

from lib.byte_budget import ByteBudget
from lib.types import OSPath

from .tacos_summary import SliceSummary


class DescribeSliceSummary:
    def it_can_construct_with_all_files_missing(self, cwd: OSPath) -> None:
        summary = SliceSummary.from_matrix_fan_out(cwd)
        assert summary == SliceSummary(
            name="(file not found: 'TF_ROOT_MODULE'",
            tf_log=["(file not found: 'tf-log.hcl'"],
            console_log=["(file not found: 'console.log'"],
            tacos_verb="(file not found: 'tacos_verb'",
            explanation="(file not found: 'explanation'",
            returncode=-1,
            url="",
        )

    def it_can_summarize_with_all_files_missing(self, cwd: OSPath) -> None:
        summary = SliceSummary.from_matrix_fan_out(cwd)
        actual = "\n".join(summary.markdown(ByteBudget(9999)))
        assert (
            actual
            == """
### (file not found: 'TF_ROOT_MODULE' <!--🌮:(file not found: 'tacos_verb'-->
(file not found: 'explanation'

<details>
<summary>Failure: error code -1</summary>
<details>
<summary>Commands: (error code -1)</summary>

```console
(file not found: 'console.log'
```
</details>

```hcl
(file not found: 'tf-log.hcl'
```
</details>
"""
        )
