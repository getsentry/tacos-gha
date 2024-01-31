correctness:

- [x] refuse apply without review
- [ ] refuse apply for closed PR
  - [ ] refuse to lock a closed PR?
- [ ] apply should ignore approval by non-codeowners
- [ ] FIXME: tf-lock-info infinite regress if providers are undeclared

ease of use (UI/UX):

- [ ] explain declined apply due to draft status
- [x] explain declined apply due to missing review
- [ ] explain declined apply due to closed PR
  - suggest re-opening the PR
- [ ] on conflict, provide a link to conflicting PR
- [ ] phased allowlist:
  1.  [x] off
  2.  [ ] plan-only
  3.  [ ] plan-and-lock
  4.  [x] plan-lock-apply
- [ ] create, show plan even for "ready" PR that can't obtain lock
- [ ] enable workflow-dispatch from master branch
- [ ] TODO: hide "commands" in PR comments when exit code is 0
- [ ] TODO: roll up init / refresh phases from tf log

testing:

- [ ] p1: How does apply work in a auto-merge situation?
  - simple: complain if auto-merge is enabled for un-applied change
  - simple: user documentation? let's dont do that
  - is it possible to disable automerge in that case?
- [ ] set a terraformer at a repo-subpath .envrc
- [ ] ensure below “Test Plan” is covered in automated tests
  - [x] create PR (”PR1”) on one of the slices; see plan in comments
  - [ ] set `🌮:apply` label on PR; recieve error message about review
  - [ ] create PR on other (non-enabled) ops slices: nothing happens; close
  - [ ] create another, conflicting PR (”PR2”)
  - [ ] see conflict error (with $USER@$PR) in comments
    - [ ] with link to conflicting PR
  - [ ] unlock PR1; update PR2; see PR2 take lock
  - [ ] merge PR2; label PR1 :taco::plan; see PR1 take lock
- [ ] demo four allowlist phases
- [ ] automated testing for lib/tf_lock
- [ ] raise XFailed("Comment not implemented yet.")
- [ ] raise XFailed("locking not yet implemented")
- [ ] raise XFailed("notify_owner action does not exist")
- [ ] raise XFailed("tacos/drift branch not created")
- [ ] raise XFailed("terraform changes not yet mergeable")
- [ ] sh.banner("TODO: check that the plan matches what we expect")
- [ ] TODO: check for the opening of the drift remediation branch.
- [ ] FIXME: automated testing for lib/tf_lock
- [ ] TODO: anything (scenario: drift detection)

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
- [ ] tf state lock auth
  - FIXME: don't use the apply terraformer for the plan workflow
  - FIXME: need a lower-privilege way to enable locking
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
