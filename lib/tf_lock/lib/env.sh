#!/not/executable/bash
set -e
export USER HOSTNAME
USER="${USER:-$(whoami)}"
HOST="${HOST:-"${HOSTNAME:-"$(hostname -f)"}"}"
HOSTNAME="$HOST"

export TF_LOCK_ENONE=2
export TF_LOCK_EHELD=3

export TACOS_GHA_HOME="${TACOS_GHA_HOME:-$(cd "$HERE"/../..; pwd)}"
export PYTHONPATH="$TACOS_GHA_HOME${PYTHONPATH:+:$PYTHONPATH}"
export PATH="$TACOS_GHA_HOME/bin${PATH:+:$PATH}}"

tf_working_dir() {
  root_module="$1"
  if [[ -e "$root_module/terragrunt.hcl" ]]; then
    terragrunt validate-inputs
    env --chdir "$root_module" terragrunt terragrunt-info |
      jq -r .WorkingDir
  else
    echo "$root_module"
  fi
}

export TERRAGRUNT_LOG_LEVEL
if [[ "${DEBUG:-}" ]]; then
  TERRAGRUNT_LOG_LEVEL=info
  set -x
else
  TERRAGRUNT_LOG_LEVEL=error
fi
