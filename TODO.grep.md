Action items in the code:

```console
$ git grep -Ei '(todo|fixme|xxx)[: ]|raise xfail'
FIXME: automated testing for lib/tf_lock
FIXME: don't use the apply terraformer for the plan workflow
FIXME: need a lower-privilege way to enable locking
FIXME: support `-u $USER` and/or `-u $EMAIL` to request an end-user access token
FIXME: this check shouldn't be disabled, but it's bugged currently,
FIXME: this really should be done in a fan-in summary job
FIXME: use a more specific type than str
FIXME: we need a better way to demarcate tf-plan in comments
FIXME: we need a fan-in summary
FIXME: we need pip packaging
TODO: Perhaps I should change my mind though, given macOS.
TODO: amend if the previous commit was a similar auto-commit
TODO: anything
TODO: centralize reused type aliases
TODO: clean up `sac-terraformer` configs, then delete me:
TODO: clean up `sudo-gcp.toml` configs, then delete me:
TODO: convert from matrix job to unlock slices "all at once"
TODO: examine the expiry timestamp of the cached token
TODO: fetch and apply the `--out tfplan` file from plan workflow
TODO: github-script to fetch run-id of the most recent tfplan
TODO: hide "commands" on exit code 0
TODO: interpolate with a python (rust?) script, for less abitrary execution
TODO: maybe check for the opening of the drift remediation branch.
TODO: maybe our "commands" should (be able to) report "already done", too?
TODO: refactor to an object that takes token in constructor, remove autouse
TODO: sh.show_json(): use jq to highlight
TODO: there should be a better way of simulating the PR being marked as abandoned.
TODO: there should be a better way of simulating the PR being marked as stale.
TODO: update actions for minimal slice names
TODO: upstream feature request on google-github-actions/auth -- this
TODO: use logging module? probs not...
def __init__(  # pyright: ignore[reportMissingSuperCall]  # TODO: bugreport
raise XFailed("Comment not implemented yet.")
raise XFailed("locking not yet implemented")
raise XFailed("notify_owner action does not exist")
raise XFailed("tacos/drift branch not created")
raise XFailed("terraform changes not yet mergeable")
raise XFailed(str(xfails))
sh.banner("TODO: check that the plan matches what we expect")
```
