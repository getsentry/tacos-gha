# Installation

To configure a GitHub repository to use TACOS-GHA, you need to configure a
number of workflows in the `.github/workflows/` directory in the repository.
Examples of these workflow files can be found [here](workflows).

# Concepts

- slice
  - A collection of terraform resources sharing a single non-local terraform
    state backend.
- lock
  - A standard terraform lock, thus visible to any tool using terraform.
- drift
  - A state where changes have been made to resources controlled by a slice
    which have not been merged into the default branch of the repository.
- action
  - A thing TACOS-GHA can do. Currently plan, apply, unlock and detect drift.
    Actions can be triggered implicitly, explicitly or on a schedule.

# Configuration

To facilitate a gradual rollout of TACOS-GHA, you can configure what slices it
is allowed to work on. This is controlled by files in the `.config/tacos-gha/`
directory in the repository. These include:

- `plan.allowlist`
  - Controls the ability to lock and plan a slice, as well as to unlock it.
- `apply.allowlist`
  - Controls the ability to apply changes to a slice. If a slice is listed here,
    it should also be listed in `plan.allowlist`.
- `drift.allowlist`
  - Controls if a slice is included in the drift detection job.
- `slices.allowlist`
  - The fallback allowlist. A slice listed here is allowed for all actions in
    TACOS-GHA.

These allowlists can consist of empty lines, comments where the first character
of the line is a #, and patterns that will be matched to slices with with
python's [fnmatch module](https://docs.python.org/3/library/fnmatch.html).

# Usage

## The Pull Request

The first step in using TACOS-GHA is to open a pull request with changes to a
slice or slices. This can be done either as a draft or as a regular pull
request. Either way, TACOS-GHA will attempt to plan the changes for the slice(s)
and post them to the pull request as a comment. This will also happen on every
push of new commits to the pull request. If the pull request is a draft,
TACOS-GHA will not attempt to lock the slice(s) for these plans, while it will
when the pull request is not a draft. If an attempt to lock the slice(s) is made
and fails, the details of the failure will be posted to the pull request as a
comment, and the plan will be aborted. If a non-draft pull request is converted
to a draft, TACOS-GHA will release any locks it holds on the slice(s) and if a
draft pull request is marked as ready for review, TACOS-GHA will attempt to lock
and plan the slice(s). Finally, if a pull request is closed, including via
merging it, TACOS-GHA will release any locks it holds on the slice(s).

To summarize:

- Opening, pushing new commits to or marking a pull request as ready for review
  will cause the slice(s) in it to be planned.
- If the pull request is not a draft, planning the slice(s) includes taking a
  lock.
- Converting the pull request to a draft or closing it will release any locks on
  the slice(s) involved.

## Conflicts

Due to the nature of GitHub Actions, TACOS-GHA cannot run on pull requests that
have merge conflicts. As a fallback, TACOS-GHA will attempt to detect this
situation and notify the user via comments and labels that it has occured. When
the merge conflict has been solved, TACOS-GHA will resume normal operation.

## Labels

Labels can be used on the pull request to cause TACOS-GHA to take action.
TACOS-GHA will also use labels to communicate its status on a pull request.

### `🌮:plan`

The `🌮:plan` label can be used to cause TACOS-GHA to plan the slice(s) involved
in a pull request. Similar to planning when opening a pull request, this will
not take locks if the pull request is a draft. This label can be useful if you
need to regenerate the plan without having changed the files involved, such as
when resources or permissions have changed outside of terraform.

### `🌮:unlock`

The `🌮:unlock` label can be used to cause TACOS-GHA to release any locks it's
holding on the slice(s) involved in a pull request. This can be useful if you
need to unlock a slice, but it isn't desirable to close the pull request or
convert it to a draft. Note that any subsequent action on the pull request that
would normally cause TACOS-GHA to take the locks will still do so.

### `🌮:apply`

The `🌮:apply` label can be used to cause TACOS-GHA to apply the slice(s)
involved in a pull request. For this to work, the pull request must not be a
draft and it must have been approved, by an appropriate CODEOWNER if the
repository settings specify that. Apply always attempts to take the lock, and
will abort the apply if it cannot. The lock is **NOT** released after the apply,
allowing subsequent plans and applies on the same pull request.

### `🌮:lock`

The `🌮:lock label is used by TACOS-GHA to indicate that the labeled pull
request holds a lock.

### `🌮:conflict`

The `🌮:conflict` label is used by TACOS-GHA to indicate that the labeled pull
request has a conflict.

## Comments

TACOS-GHA presents some output to the user via comments on pull requests. To the
best of its ability it will attempt to deduplicate and reuse its comments.

## Drift Detection/Remediation

On a daily schedule, TACOS-GHA will check for drift in all slices. If it finds
any, it will open a pull request for those slices, thus taking the locks.
