correctness:

- [ ] refuse apply without review

ease of use (UI/UX):

- [ ] explain declined applies (due to draft or due to review)

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
