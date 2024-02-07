# who can do what

- only the original pr author (USER=github.triggering_actor)
  - apply
    - the original author is the responsible party for all prod changes
  - taco::unlock
    - to steal the lock, you must close the PR
    - could then reopen PR of the same branch, to transfer ownership
- anyone that has the relevant github permission
  (USER=github.event.pull_request.user.login) set this as default?
  - taco::plan
  - close pr -> unlock # this serves as force unlock
  - convert to draft -> unlock
  - convert to ready -> lock
  - commit -> plan (and lock)
  - merge -> close -> unlock
    - make "apply" a required check -- must pass for irrelevant PRs
