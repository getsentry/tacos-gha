#!/not/executable/bash
set -e
export TACOS_HOME
TACOS_HOME="${TACOS_HOME:-$(cd "$HERE/"../..; pwd)}"

export USER HOSTNAME
USER="${USER:-$(whoami)}"
HOST="${HOST:-"${HOSTNAME:-"$(hostname -f)"}"}"
HOSTNAME="$HOST"

export TF_LOCK_ENONE=2
export TF_LOCK_EHELD=3
