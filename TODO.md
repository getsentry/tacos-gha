# TODO

## Major Milestones

### Milestone 2: Maintainability Improvements

Definition: All tacos-gha work beyond this milestone work is optional and can be
done on a 20%-time basis. (But, to be clear, this milestone is non-optional.)

- commitment: 2024-04-03
- goal: 2024-03-20
- assignees @50% time: buck ellison neo?

- [~] @ellison user guide
  - how-to: avoid GHA notification spam
  - https://github.com/getsentry/tacos-gha/pull/168
- [ ] @buck run tests in CI -- stretch
- [ ] convert the rest of the sh to python
      https://github.com/getsentry/tacos-gha
  - @ian: "I'll look and take some part of it"
  - use `./lib/git/ls-sh` for a listing
  - [ ] lib/ci/bin
  - [ ] lib/ci
  - [ ] lib/gcloud
  - [ ] lib/github_actions
  - [ ] lib/unix/super
  - [ ] lib/unix/quietly
  - [ ] lib/unix/tty-attach

## Milestone 3: entering "maintenance mode"

These are what we believe are the minimum requirements for tacos-gha to be
considered "maintenance mode". There are a couple bugs and some maintainability
issues to be fixed.

- [ ] ownership/stewardship transition
  - [ ] @ellison developer's guide
    - HACKING.md ?
  - [ ] onboard a new team member from SRE
    - neo dmitrii jim richard
    - [x] invite to standup
- [~] @neo bug: unlock after removing changes can result in orphaned locks

  - the Right Way: our cached state file PR -- work in progress
    - latest news: testing under ops repo
    - matrix fan-in/out funniness
  - the Quick Fix: when taking a lock fails, double-check if it's from a closed
    PR and force it unlocked if so. This isn't the right fix, but it's Good
    Enough for today and easy to implement.

- [~] @ellison schedule a friday burn-down working meeting

- [ ] run test suite in CI

  - put op github-app secrets into gha secrets
  - may need some security-as-code stuff to authorize gcloud?

- [~] @maxwell datadog ops events

  - remove the `if-not-ci` wrapper and it _may_ just work? `git grep if-not-ci`
  - the core code for this in sentry-kube can be (needs to be) extracted to a
    separate module with only stdlib dependencies
  - we can't spend five minutes installing sentry-kube dependencies under GHA

- [~] @ellison fix test suite -- update to new tag style, used in combined plan
  summary

- [ ] run test suite in CI

  - put op github-app secrets into gha secrets
  - may need some security-as-code stuff to authorize gcloud?

- [ ] :tacos::unlock should not cancel convert-to-draft

  - currently, the label can cause the unlock job (spawned by the "convert to
    draft button") to be cancelled (and not run at all)
  - remove :tacos::unlock in favor of convert-to-draft
  - deprecation phase: post a PR comment about "convert to draft instead"

- low-hanging and/or important UI enhancement requests:

  - [ ] Make it much more clear that the lock was taken
  - [ ] Make it clear why the lock was taken
  - [ ] Leave a breadcrumb to User's Guide
  - [ ] set an "unlock in progress" message in the PR (use the mode:delete
        option) #good-first-pr
    - [ ] similarly, for plan
    - [ ] similarly, for apply
  - [ ] provide a good, human-readable PR message for unlock failure

- [ ] @ellison down the old terraform-plan workflow

### (Future Work) Milestone 4: Drift Remediation

Definition: All ops slices are subject to TACOS lock when drift is present.

- [ ] drift remediation

  - [?] @ellison phased allowlist:
    https://github.com/getsentry/tacos-gha/pull/119

    1.  [x] off
    2.  ~[wontfix] plan-only~
    3.  [ ] plan-and-lock
    4.  [x] plan-lock-apply
    5.  [ ] drift detection

  - [x] @neo ensure lock conflict message links to the lock-holding PR

    - essential for people know when there's conflicting drift

  - fix TODOs found in the code:

    - [ ] `raise XFailed("tacos/drift branch not created") branch?`
    - [ ] `TODO: check for the opening of the drift remediation branch.`
    - [ ] `TODO: anything (scenario: drift detection)`

# Open Questions

We still need to talk about these items more.

- after full rollout and acceptance
  - [?] how will people know when there's _new_ drift?
    - will need to reconsider once we have more user experience
    - initial implementation: people need to notice the automatic drift pr
    - slack notification?
    - team-sre needs to decide

# Categories

Future action items organized into broad categories. These should be done "some
day" but currently have no firm plan of action.

## Ease of Use (UI/UX)

P2

- [ ] speed - minimize time to plan, round-trip

  - [ ] optimize setup action
  - [ ] optimize list-slices action
    - can we get just the filenames of _.hcl _.tf files?
    - then we can touch empty files, simulate a clone for
      determine-relevant-slices
  - [ ] leverage "narrow" git clones, where possible
  - [ ] commit pre-calculated data to the repo? for example:
    - terraform backend configuration (lock location)
    - must be automatically updated

- [ ] create, show plan even for "ready" PR that can't obtain lock
- [ ] P3 @ian Node 16 deprecation warnings
  - https://github.com/getsentry/ops/actions/runs/7849633666
- [ ] leave a link to the job that produced the log shown in comment
  - example:
    https://github.com/getsentry/tacos-gha/actions/runs/7890053512/job/21531390874
    https://github.com/$org/$repo/actions/runs/$runid/job/$jobid
  - [ ] @ian research: how to get the "job id" during a job?
  - [x] @buck in tacos-gha.demo
  - [ ] in ops repo -- default gha identities have less permissions in private
        repo something something?

## Testing

### Tier 1

P1

We keep breaking these

- [ ] terragrunt slice with dependencies
  - prevent regression: --terragrunt-no-auto-init was exploding during
    terragrunt-info
- [ ] "bare" terragrunt slices (AKA ops-repo style, `source`d slices)

P2

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

### Tier 2

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

# Future Improvements

These may never happen, but that's okay.

- [ ] add a github app with `repo` permission so that we can enable deep-link
      per-slice in PR comments
- [ ] TODO: fetch and apply the `--out tfplan` file from plan workflow
- [ ] TODO: github-script to fetch run-id of the most recent tfplan
- [ ] FIXME: use a more specific type than str
- [ ] TODO: workflow to automatically add taco:stale label as appropriate
- [ ] TODO: workflow to automatically add taco:abandoned label as appropriate
- [ ] integrate TACOS into terraform-sandbox repo:
      https://github.com/getsentry/terraform-sandboxes.private
  - this will help kickstart #proj-clickops
- [ ] convert lib/tf-lock to use the (private!?) golang api
  - will need to fork terraform -- it's the only way to force un-private in go
  - this will help with several issues:
    - listing all locked slices efficiently
    - locking slices efficiently (don't need to kill -9 terraform-console)
    - retrieving lock info (don't need to parse `terraform force-unlock` errors)
    - setting lock info (no need for .github/actions/set-user-and-hostname)
- [ ] P2/3 lock and plan downstream terragrunt dependencies too? needs more
      discussion
- [ ] TODO: convert from matrix job to unlock slices "all at once"
  - @neo attempted but it took ~7 minutes to run the unlock job
    https://github.com/getsentry/ops/pull/9859

## Epics

- [ ] pip packaging
  - FIXME: we need pip packaging
- [ ] TODO: interpolate with a python (rust?) script, for less abitrary
      execution

## Upstream

I need to file upstream bugs for these. The maintainers would want to know and
fix them, I think.

- def **init**( # pyright: ignore[reportMissingSuperCall] # TODO: bugreport
- upstream feature request on google-github-actions/auth -- this

## nice-to-have

AKA "probably not"

```
TODO: refactor to an object that takes token in constructor, remove autouse
TODO: update actions for minimal slice names
TODO: examine the expiry timestamp of the cached token
TODO: clean up `sac-terraformer` configs, then delete me:
TODO: clean up `sudo-gcp.toml` configs, then delete me:
TODO: amend if the previous commit was a similar auto-commit
```

## Long Term Goals

onboard preexisting users:

- getsentry/security-as-code
  - replace reusable-plan and reusable-apply with tacos-gha
  - ci, cd become callers to tacos-gha
- getsentry/security-fleetdm/.github/workflow/{ci,cd}
- getsentry/terraform-sandbox/.github/workflow/{ci,cd}
- getsentry/eng-pipes
- getsentry/devenv-deployment-service

# off topic

These items need to live elsewhere

- [ ] TSC presentation about IAM long-term

# legend:

- not started: [ ]
- in progress: [~]
- done: [x]
- needs more discussion: [?]
