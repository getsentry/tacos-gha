#!/sourceme/bash
_here="$(readlink -f "$(dirname "${BASH_SOURCE:-$0}")")"

export TACOS_GHA_HOME="$_here"

if ! command -v flock &> /dev/null; then
    echo "flock is not installed. Running make..."
    make -C "$TACOS_GHA_HOME" .done/brew
fi

export PATH="$TACOS_GHA_HOME/bin${PATH:+:$PATH}}"


unset _here
