#!/bin/bash
# This script represents a "worst case" (but valid) use case.
# Receive merged fan-in data from fan-out jobs, but also some auxilliary data.
set -euo pipefail
exec >&2  # our only output is logging
HERE="$(dirname "$(readlink -f "$0")")"
fan_in="**/$MY_MATRIX_IO_DIR"

set -x
sum=$(
  find "$fan_in" -type f -name 'matrix*json' -print0 |
    xargs -0 jq -s add
)

# >>> sum([(i**2 + 1) for i in range(1, 31)])
#expected=9485
expected=$((
  1 + 10**2 +
  1 + (10/5)**2 +
  1 + 27**2 +
  1 + (27/5)**2
))
if (( sum != expected )); then
  echo "FAIL: sum should be $expected, got $sum"
  exit 123  # convention borrowed from xargs -- a test failed
fi

find "$fan_in" -type f -name 'random.txt' -print0 | xargs -0 head
find "$fan_in" -type f -name 'random.json' -print0 | xargs -0 jq .
find "$fan_in" -type f -name 'key.json' -print0 | xargs -0 cat | sort -n

"$HERE/"selftest-summary.sh "$fan_in"
