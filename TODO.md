action items:

- [ ] bug: committing to another persons's pr fails locking
- [x] security issue
- [ ] wide rollout & comms
- [ ] jira ticket for bucket permissions
- [ ] backlog to fix test-region bucket
- [ ] user guide
  - notification adjustment
- about drift detection
  - [ ] allowlist config
- [ ] fix the test suite
- [ ] run tests in CI -- stretch
- [ ] drift remediation -- how will people know when there's a new drift branch?
  - ensure lock conflict message links to the lock-holding PR
- [ ] down the old terraform-plan workflow
  - after full rollout

correctness:

- [x] refuse apply without review
  - [x] @buck apply should ignore approval by non-codeowners
    - i.e. check mergability instead of approvers
- [x] @ellison refuse apply for closed PR
  - [x] explain declined apply due to closed PR
    - suggest re-opening the PR
- [ ] @ellison unlock even if closed with merge conflicts
  - let user know why nothing is going to happen
- [x] @ellison unlock even if closed by another user
  - set username from pr author on closed event
- [x] @buck P3: FIXME: tf-lock-info infinite regress if providers are undeclared

security:

- [x] tf state lock auth -- @trostel has confirmed P2 priority
  - FIXME: don't use the apply terraformer for the plan workflow
  - FIXME: need a lower-privilege way to enable locking

ease of use (UI/UX):

- [ ] @ellison user guide
- [ ] speed - minimize time to plan, round-trip
  - [ ] optimize setup action
  - [ ] optimize list-slices action
    - can we get just the filenames of _.hcl _.tf files?
    - then we can touch empty files, simulate a clone for
      determine-relevant-slices
  - [ ] leverage "narrow" git clones, where possible
- [x] explain declined apply due to draft status
- [x] explain declined apply due to missing review
- [ ] on conflict, provide a link to conflicting PR
- [ ] @ellison phased allowlist:
  1.  [x] off
  2.  [ ] plan-only
  3.  [ ] plan-and-lock
  4.  [x] plan-lock-apply
- [ ] create, show plan even for "ready" PR that can't obtain lock
- [x] @buck TODO: roll up "commands" in PR comments when exit code is 0
- [x] @buck TODO: roll up init / refresh phases from tf log
- [ ] P3: Tell user that merge conflicts are preventing plan/apply

testing: (tier 1)

- [ ] terragrunt slice with dependencies
  - prevent regression: --terragrunt-no-auto-init was exploding during
    terragrunt-info
- [ ] run _something_ with debug mode active
- [ ] ensure below “Test Plan” is covered in automated tests
  - [x] create PR (”PR1”) on one of the slices; see plan in comments
  - [ ] set `🌮:apply` label on PR; recieve error message about review
  - [ ] create PR on other (non-enabled) ops slices: nothing happens; close
  - [ ] create another, conflicting PR (”PR2”)
  - [ ] see conflict error (with $USER@$PR) in comments
    - [ ] with link to conflicting PR
  - [ ] unlock PR1; update PR2; see PR2 take lock
  - [ ] merge PR2; label PR1 :taco::plan; see PR1 take lock
- [ ] raise XFailed("locking not yet implemented")
- [ ] raise XFailed("Comment not implemented yet.")
- [ ] explain declined apply due to closed PR

testing: (tier 2)

- [ ] refuse apply without review
- [ ] p1: How does apply work in a auto-merge situation?
  - simple: complain if auto-merge is enabled for un-applied change
  - simple: user documentation? "dont do that"
  - is it possible to disable automerge in that case?
- [ ] set a terraformer at a repo-subpath .envrc
- [ ] demo four allowlist phases
- [ ] automated testing for lib/tf_lock -- see lib/tf_lock/TESTING.md
- [ ] raise XFailed("notify_owner action does not exist")
- [ ] raise XFailed("terraform changes not yet mergeable")
- [ ] FIXME: automated testing for lib/tf_lock
- [ ] sh.banner("TODO: check that the plan matches what we expect")
- [ ] TODO: check for the opening of the drift remediation branch.
- [ ] TODO: anything (scenario: drift detection)
- [ ] raise XFailed("tacos/drift branch not created")

future improvements:

- [ ] TODO: fetch and apply the `--out tfplan` file from plan workflow
- [ ] TODO: github-script to fetch run-id of the most recent tfplan
- [ ] TODO: convert from matrix job to unlock slices "all at once"
- [ ] FIXME: use a more specific type than str
- [ ] TODO: workflow to automatically add taco:stale label as appropriate
- [ ] TODO: workflow to automatically add taco:abandoned label as appropriate

epics:

- [ ] pip packaging
  - FIXME: we need pip packaging
- [ ] summary steps
  - FIXME: we need a fan-in summary
  - FIXME: this really should be done in a fan-in summary job
- [ ] TODO: interpolate with a python (rust?) script, for less abitrary
      execution

upstream:

- def **init**( # pyright: ignore[reportMissingSuperCall] # TODO: bugreport
  TODO:
- upstream feature request on google-github-actions/auth -- this

nice-to-have: (AKA "probably not")

```
TODO: refactor to an object that takes token in constructor, remove autouse
TODO: update actions for minimal slice names
TODO: examine the expiry timestamp of the cached token
TODO: clean up `sac-terraformer` configs, then delete me:
TODO: clean up `sudo-gcp.toml` configs, then delete me:
TODO: amend if the previous commit was a similar auto-commit
```

### Long Term Goals

onboard preexisting users:

- getsentry/security-as-code
  - replace reusable-plan and reusable-apply with tacos-gha
  - ci, cd become callers to tacos-gha
- getsentry/security-fleetdm/.github/workflow/{ci,cd}
- getsentry/terraform-sandbox/.github/workflow/{ci,cd}
- getsentry/eng-pipes
- getsentry/devenv-deployment-service
