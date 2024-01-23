#!/not/executable/bash
set -eEuo pipefail
trap 'echo ERROR '\''(code:$?)'\' ERR

# NB: aliases must be defined before their call-site is *parsed*
shopt -s expand_aliases
alias set+x='{ set +x; } 2>/dev/null'

unset DIRENV_DIFF  # whatever envrc we've run is our basis from now on

direnv() {
  : bring in environment config vars
  set+x  # direnv output is very noisy

  command direnv allow
  eval="$(command direnv export bash)"
  eval "$eval"

  set -x
}

cd() {
  set+x
  builtin cd "$@"
  set -x
  direnv
}
