Action items in the code:

```console
$ git grep -Ei '(todo|fixme|xxx)[: (]|raise xfail'
":taco::plan"  # FIXME: add, use a :taco::lock label
FIXME: automated testing for lib/tf_lock
FIXME: matrix-fan-in/rename-tmp should really be python
FIXME: only use state-admin access for a locking (non-draft) plan
FIXME: support `-u $USER` and/or `-u $EMAIL` to request an end-user access token
FIXME: this check shouldn't be disabled, but it's bugged currently,
FIXME: this is "right" but it causes stdio deadlock D:
FIXME: this really should be done in a fan-in summary job
FIXME: use a more specific type than str
FIXME: we need a fan-in summary
FIXME: we need pip packaging
TODO(P3): refactor to an object that takes token in constructor
TODO(P3): sh.show_json(): use jq to highlight
TODO: I was forced to typo the name to avoid a "unknown hook" error
TODO: amend if the previous commit was a similar auto-commit
TODO: anything (scenario: drift detection)
TODO: apparently pytest calls resume() once per test during discovery?
TODO: auto-configure terragrunt retry patterns in tacos-gha
TODO: check for the opening of the drift remediation branch.
TODO: clean up `sac-terraformer` configs, then delete me:
TODO: clean up `sudo-gcp.toml` configs, then delete me:
TODO: convert from matrix job to unlock slices "all at once"
TODO: examine the expiry timestamp of the cached token
TODO: fetch and apply the tfplan artifact from plan workflow
TODO: figure out a sane way to export this as a contextmanager, too
TODO: github-script to fetch run-id of the most recent tfplan
TODO: improve the conflict message: "lock failed, on slice prod/slice-3-vm, due to user1, PR #334 "
TODO: interpolate with a python (rust?) script, for less abitrary execution
TODO: let the user know plan may not be fully accurate, if they dont have the lock
TODO: let the user know who has the lock
TODO: make "apply" a required check -- must pass for irrelevant PRs
TODO: make use of lib.patch, to replace ad-hoc monkeypatching
TODO: update actions for minimal slice names
TODO: upstream feature request on google-github-actions/auth -- this
TODO: workflow to automatically add taco:abandoned label as appropriate
TODO: workflow to automatically add taco:stale label as appropriate
TODO: you'll probably want to rewrite this as a python thread someday
def __init__(  # pyright: ignore[reportMissingSuperCall]  # TODO: bugreport
raise XFailed("close-on-dirty comment not implemented yet.")
raise XFailed("notify_owner action does not exist")
raise XFailed("tacos/drift branch not created")
sh.banner("TODO: check that the plan matches what we expect")
```
