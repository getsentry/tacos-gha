# who can do what

- only the original pr author allowed, so identity set to user trying the action
  (USER=github.triggering_actor)
  - apply
    - the original author is the responsible party for all prod changes
  - taco::unlock
    - to steal the lock, you must close or draft the PR
      - could then reopen PR of the same branch, to transfer ownership
- anyone that has the relevant github permission, so identity set to original
  author (USER=github.event.pull_request.user.login)
  - workflow: plan
    - taco::plan
    - convert to ready -> plan (and lock)
    - commit -> plan (and lock)
    - reopen -> plan (and lock)
  - workflow: unlock
    - close pr -> unlock # this serves as force unlock
    - convert to draft -> unlock
    - merge -> close -> unlock
      - TODO: make "apply" a required check -- must pass for irrelevant PRs
