# TODONE

These were TODO items, but now they're TODONE. :cookie:

# Milestones

(reverse-chronological order, please)

## Milestone 1: Wide Rollout

P1

Definition: All ops slices are subject to TACOS lock-on-PR.

- commitment: 2024-03-06
- goal: 2024-02-28
- assignees: buck ellison neo

* [x] wide rollout & comms -- use TACOS by default for all ops slices

  - [x] @buck combined summary comments
    - [x] we need a fan-in summary
    - [x] @neo fan-in summary for the tacos_unlock workflow
  - [x] @filippo jira ticket for bucket permissions
    - https://gist.github.com/bukzor/ee00a6f75d4a0cc7f865c37cfa67a895
    - https://getsentry.atlassian.net/browse/OPS-5203
  - [x] @ellison clickops quickfix test-region bucket
    - https://gist.github.com/bukzor/ee00a6f75d4a0cc7f865c37cfa67a895
  - [x] @ellison Tell user that merge conflicts are preventing plan/apply
  - [x] @ellison JIRA backlog to tf-import test-region bucket IAM
    - gs://sentry-test-region-terraform
    - https://getsentry.atlassian.net/browse/OPS-5244
  - [x] @ellison new permissions issues
    - in review: https://github.com/getsentry/ops/pull/9733
    - ability to look at machine images for spinning up new instances
    - need to grant something to the team-sre terraformer
  - [x] @jim ops fixes to project & bucket permissions
    - https://getsentry.atlassian.net/browse/OPS-5203

## milestone zero: MVP

### Correctness

P1

- [x] @ellison bug: committing to another persons's pr fails locking
- [x] refuse apply without review
  - [x] @buck apply should ignore approval by non-codeowners
    - i.e. check mergability instead of approvers
- [x] @ellison refuse apply for closed PR
  - [x] explain declined apply due to closed PR
    - suggest re-opening the PR
- [x] @ellison unlock even if closed by another user
  - set username from pr author on closed event
- [x] @buck P3: FIXME: tf-lock-info infinite regress if providers are undeclared
- [x] combined messages, like plan
  - [x] @neo unlock
  - [x] @neo apply

# Categories

These were done apart from any particular milestone

## Ease of Use (UI/UX)

P2

- [x] explain declined apply due to draft status
- [x] explain declined apply due to missing review
- [x] @buck TODO: roll up "commands" in PR comments when exit code is 0
- [x] @buck TODO: roll up init / refresh phases from tf log

## Security

- [x] @buck security issue
  - [x] tf state lock auth -- @trostel has confirmed P2 priority
    - fixed: don't use the apply terraformer for the plan workflow
    - fixed: need a lower-privilege way to enable locking
