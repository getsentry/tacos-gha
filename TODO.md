testing:

1. environment fixture
1. chdir fixture
1. PR fixture, with cleanup
1. unit tests for all lib/ functions

auth:

1. create role-ops-planner / applier roles
2. add roles to ops bucket(s)

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
