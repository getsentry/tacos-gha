#!/bin/bash
# This script represents a "worst case" (but valid) use case.
# Send more than one json to fan-in, as well as some auxilliary data, via a
# non-default path.

set -euo pipefail
exec >&2  # our only output is logging
HERE="$(readlink -f "$(dirname "$0")")"

gha-set-output() {
  var="$1"
  val="$(cat)"
  tee -a "$GITHUB_OUTPUT" <<< "$var=$val"
}
gha-set-artifact() {
  artifact="$1"
  gha-set-output "artifact.$artifact" <<< "$artifact"

  if ! [[ -e "$artifact" ]]; then
    cat > "$artifact"
  fi
}

key="$1"

set -x

: Processing... "$key"

gha-set-output key <<< "$key"
echo "title=Hello, $key!" | tee -a "$GITHUB_OUTPUT"

"$HERE/"square.py "$key" |
  gha-set-artifact square.txt

square=$((key ** 2))
echo "$square" | gha-set-output 'matrix.json'

outdir="x/y/z"
mkdir -p "$outdir"
gha-set-artifact "x"

echo 1 > "x/y/matrix.1.json"
echo "$RANDOM" | tee "x/random.txt" "x/y/z/random.json"

find "$outdir" -type f -print0 | xargs -0 head
