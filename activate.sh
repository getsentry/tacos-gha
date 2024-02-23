#!/sourceme/bash
_here="$(readlink -f "$(dirname "$0")")"

export TACOS_GHA_HOME="$_here"
export PATH="$TACOS_GHA_HOME/bin${PATH:+:$PATH}}"

unset _here