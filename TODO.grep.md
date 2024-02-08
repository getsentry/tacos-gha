Action items in the code:

```console
$ git grep -Ei '(todo|fixme|xxx)[: (]|raise xfail'
FIXME: a lower-privilege way to authorize tf-init
FIXME: only use state-admin access for a locking (non-draft) plan
FIXME: support `-u $USER` and/or `-u $EMAIL` to request an end-user access token
FIXME: this check shouldn't be disabled, but it's bugged currently,
FIXME: this really should be done in a fan-in summary job
FIXME: use a more specific type than str
FIXME: we need a fan-in summary
FIXME: we need pip packaging
TODO(P3): refactor to an object that takes token in constructor, remove autouse
TODO(P3): sh.show_json(): use jq to highlight
TODO: amend if the previous commit was a similar auto-commit
TODO: anything (scenario: drift detection)
TODO: auto-configure terragrunt retry patterns in tacos-gha
TODO: check for the opening of the drift remediation branch.
TODO: clean up `sac-terraformer` configs, then delete me:
TODO: clean up `sudo-gcp.toml` configs, then delete me:
TODO: convert from matrix job to unlock slices "all at once"
TODO: examine the expiry timestamp of the cached token
TODO: fetch and apply the tfplan artifact from plan workflow
TODO: github-script to fetch run-id of the most recent tfplan
TODO: interpolate with a python (rust?) script, for less abitrary execution
TODO: let the user know plan may not be fully accurate
TODO: let the user know who has the lock
TODO: update actions for minimal slice names
TODO: upstream feature request on google-github-actions/auth -- this
TODO: workflow to automatically add taco:abandoned label as appropriate
TODO: workflow to automatically add taco:stale label as appropriate
def __init__(  # pyright: ignore[reportMissingSuperCall]  # TODO: bugreport
raise XFailed("Comment not implemented yet.")
raise XFailed("locking not yet implemented")
raise XFailed("notify_owner action does not exist")
raise XFailed("tacos/drift branch not created")
sh.banner("TODO: check that the plan matches what we expect")
```
