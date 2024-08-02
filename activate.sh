#!/sourceme/bash
_here="$(readlink -f "$(dirname "${BASH_SOURCE:-$0}")")"

export TACOS_GHA_HOME="$_here"
export PATH="$TACOS_GHA_HOME/bin${PATH:+:$PATH}}"
export DEBUG="${DEBUG:-}"

if ! flock -h >/dev/null; then
    echo "Installing missing dependencies... (flock)"
    make -C "$TACOS_GHA_HOME" .done/brew
fi

unset _here
