### 2023-12-21 w/ buck and asottile

- custom actions
  - asottile recommends pure-python, stdlib-only composite actions, over js
    actions (https://github.com/deadsnakes/action/blob/main/action.yml for
    example)
    - example with multiple actions:
      https://github.com/asottile/workflows/tree/main/.github/actions
    - usage:
      https://github.com/asottile/workflows/blob/a4af24bf81590ee30b58703c2bd7e3e633ff3372/.github/workflows/tox.yml#L33
- prefer custom-actions over reusable workflows reusable
  - workflows only where you would literally copy-paste entire workflows
    - e.g. if you're always going to use tox the same exact way you'd write a
      tox reusable workflow and use that
  - custom actions are composable whereas workflows aren't
  - perhaps write a custom workflow for the most-common cases but offer custom
    actions where you need to vary
