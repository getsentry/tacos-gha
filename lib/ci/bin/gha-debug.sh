#!/sourceme/bash
# handle debugging concerns in GHA

set -x
: gha-debug.sh START

export DEBUG GH_DEBUG
DEBUG="${DEBUG:-}"
if ! [[ "$DEBUG" ]]; then
  DEBUG="${RUNNER_DEBUG:-0}"
  gha-set-env DEBUG <<< "$DEBUG"

  if (( DEBUG >= 2 )); then
    set -x
  fi

  if (( DEBUG >= 1 )); then
    # ask gh cli to show what's going on at api level
    GH_DEBUG="api"
  else  #if (( DEBUG <= 0 )); then
    GH_DEBUG=""
  fi
  gha-set-env GH_DEBUG <<< "$GH_DEBUG"

  if (( DEBUG < 3 )); then
    # fixme: this doens't do anything :(
    # turn off the spammy purple context-debugging text
    gha-set-env RUNNER_DEBUG <<< ""
    gha-set-env ACTIONS_RUNNER_DEBUG <<< ""
    gha-set-env ACTIONS_STEP_DEBUG <<< ""
  fi
fi

: gha-debug.sh END
