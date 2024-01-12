#!/not/executable/bash
set -e
export USER HOSTNAME
USER="${USER:-$(whoami)}"
HOST="${HOST:-"${HOSTNAME:-"$(hostname -f)"}"}"
HOSTNAME="$HOST"

export TF_LOCK_ENONE=2
export TF_LOCK_EHELD=3
