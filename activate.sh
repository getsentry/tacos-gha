#!/sourceme/bash
_here="$(readlink -f "$(dirname "${BASH_SOURCE:-$0}")")"

export TACOS_GHA_HOME="$_here"

    echo "Installing missing dependencies... (flock)"

export PATH="$TACOS_GHA_HOME/bin${PATH:+:$PATH}}"


unset _here
