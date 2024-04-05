#!/not/executable/bash
set -eEuo pipefail
export USER HOSTNAME
USER="${USER:-$(whoami)}"
HOST="${HOST:-"${HOSTNAME:-"$(hostname -f)"}"}"
HOSTNAME="$HOST"

export TF_LOCK_ENONE=2
export TF_LOCK_EHELD=3

export TACOS_GHA_HOME="${TACOS_GHA_HOME:-$(cd "$HERE"/../..; pwd)}"
export PYTHONPATH="$TACOS_GHA_HOME${PYTHONPATH:+:$PYTHONPATH}"
export PATH="$TACOS_GHA_HOME/lib/tf_lock/bin:$TACOS_GHA_HOME/bin${PATH:+:$PATH}}"

tf_working_dir() {
  set -eEuo pipefail

  root_module="$1"
  if [[ -e "$root_module/terragrunt.hcl" ]]; then
    ( cd "$root_module"
      # validate-inputs makes terragrunt generate its templates
      terragrunt  --terragrunt-no-auto-init=false validate-inputs

      terragrunt  --terragrunt-no-auto-init=false terragrunt-info |
        jq -r .WorkingDir
    )
  else
    echo "$root_module"
  fi
}

if [[ "${DEBUG:-}" ]]; then
  set -x
fi
