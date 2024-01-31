correctness:

- [ ] refuse apply without review

testing:

- [ ] tacos-gha.demo should set a terraformer at a repo-subpath .envrc

ease of use (UI/UX):

- [ ] explain declined applies (due to draft or due to review)

from the code:

```console


$ git grep -Ei 'xfail|todo|fixme|xxx'
.github/actions/setup/action.yml:        # TODO: upstream feature request on google-github-actions/auth -- this
.github/actions/setup/action.yml:        # TODO: upstream feature request on google-github-actions/auth -- this
.github/workflows/tacos_apply.yml:      # TODO fetch the `--out tfplan` file from the plan workflow, to use here
.github/workflows/tacos_apply.yml:      ###     # TODO: github-script to fetch run-id of the most recent tfplan
.github/workflows/tacos_apply.yml:  # FIXME: we need a fan-in summary
.github/workflows/tacos_plan.yml:# FIXME: don't use the apply terraformer for the plan workflow
.github/workflows/tacos_plan.yml:  # FIXME: we need a fan-in summary
.github/workflows/tacos_unlock.yml:# FIXME: don't use the apply terraformer for the plan workflow
.shellcheckrc:# TODO: Perhaps I should change my mind though, given macOS.
.shellcheckrc:# FIXME: this check shouldn't be disabled, but it's bugged currently,
Makefile:# TODO: maybe our "commands" should (be able to) report "already done", too?
lib/ci/lock-acquisition-comment.js:      // FIXME: need to let them know who has the lock, if you can
lib/ci/tacos-apply:# TODO: hide "commands" on exit code 0
lib/ci/tacos-detect-drift:# FIXME: this really should be done in a fan-in summary job
lib/ci/tacos-plan:  : FIXME: need a lower-privilege way to enable locking
lib/ci/tacos-plan:# TODO: hide "commands" on exit code 0
lib/gcloud/gcloud-auth-export-access-token:  # TODO: examine the expiry timestamp of the cached token
lib/gcloud/sudo-gcp:# FIXME: support `-u $USER` and/or `-u $EMAIL` to request an end-user access token
lib/gcloud/sudo-gcp-service-account:  # TODO: interpolate with a python (rust?) script, for less abitrary execution
lib/gcloud/sudo-gcp-service-account:# TODO: clean up `sudo-gcp.toml` configs, then delete me:
lib/gcloud/sudo-gcp-service-account:# TODO: clean up `sudo-gcp.toml` configs, then delete me:
lib/gcloud/sudo-gcp-service-account:# TODO: clean up `sac-terraformer` configs, then delete me:
lib/github-app/device-flow/tacos-gha-author/client-secret:FIXME: store and retrieve from 1p
lib/github-app/device-flow/tacos-gha-reviewer/client-secret:FIXME: store and retrieve from 1p
lib/pytest/cap1fd.py:    def __init__(  # pyright: ignore[reportMissingSuperCall]  # TODO: bugreport
lib/sh/cd.py:# TODO: centralize reused type aliases
lib/sh/io.py:# TODO: use logging module? probs not...
lib/tacos/slices:# FIXME: we need pip packaging
lib/tf_lock/TESTING.md:FIXME: automate
lib/tf_lock/tf-lock-release:# FIXME: we need pip packaging
lib/tf_lock/tf_lock.py:    # TODO: sh.show_json(): use jq to highlight
pyproject.toml:xfail_strict = true


```

terragrunt:

- lets do less repos?
- don't need modules for un-reused bits
- \_'d files
- ellison's linting doesn't detect (e.g.) un-pinned null provider
- rename top-level terragrunt.hcl to terragrunt-main.hcl
- does pre-commit even work w/o .tf files?

onboard preexisting users:

- getsentry/security-as-code
  - replace reusable-plan and reusable-apply with tacos-gha
  - ci, cd become callers to tacos-gha
- getsentry/security-fleetdm/.github/workflow/{ci,cd}
- getsentry/terraform-sandbox/.github/workflow/{ci,cd}
- getsentry/eng-pipes
- getsentry/devenv-deployment-service

known bugs:

- need to retry this kind of failure:
  https://github.com/getsentry/tacos-gha.demo/actions/runs/7241524637/job/19725734049#step:8:834
  ```
  Plan: 2 to add, 0 to change, 0 to destroy.
  time=2023-12-17T23:01:47Z level=info msg=╷
  │ Error: Failed to query available provider packages
  │
  │ Could not retrieve the list of available versions for provider
  │ hashicorp/null: could not query provider registry for
  │ registry.terraform.io/hashicorp/null: stream error: stream ID 1;
  │ INTERNAL_ERROR; received from peer
  ╵
  ```
