#!/bin/bash
set -euo pipefail
# This script represents a "worst case" (but valid) use case.
# Receive merged fan-in data from fan-out jobs, but also some auxilliary data.

set -euo pipefail
exec >&2  # our only output is logging

set -x
sum=$(jq -r 'to_entries | map(.value) | add' a/b/c/matrix.json)

# >>> sum([(i**2 + 1) for i in range(1, 31)])
expected=9485
#expected=$(( 3**2 + 1 + 10**2 + 1 ))
if (( sum != expected )); then
  echo "FAIL: sum should be $expected, got $sum"
  exit 123  # convention borrowed from xargs -- a test failed
fi

find a/b/c -type f -name 'random.txt' -print0 | xargs -0 head
find a/b/c -type f -name 'random.json' -print0 | xargs -0 jq .
find a/b/c -type f -name 'key.json' -print0 | xargs -0 cat | sort -n
