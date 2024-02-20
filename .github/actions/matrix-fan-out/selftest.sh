#!/bin/bash
# This script represents a "worst case" (but valid) use case.
# Send more than one json to fan-in, as well as some auxilliary data, via a
# non-default path.

set -euo pipefail
exec >&2  # our only output is logging

gha-set-output() {
  var="$1"
  val="$(cat)"
  tee -a "$GITHUB_OUTPUT" <<< "$var=$val"
}
gha-set-artifact() {
  artifact="$1"
  gha-set-output "artifact.$artifact" <<< "$artifact"
  cat > "$artifact"
}

key="$1"

set -x

: Processing... "$key"

gha-set-output key <<< "$key"
echo "title=Hello, $key!" | tee -a "$GITHUB_OUTPUT"

"$GITHUB_ACTION_PATH/"square.py "$key" |
  gha-set-artifact square.txt

square=$((key ** 2))
echo "$square" | gha-set-output 'matrix'

outdir="a/b/c"
gha-set-artifact "$outdir"

mkdir -p "$outdir/x/y/z"
echo 1 > "$outdir/x/y/matrix.1.json"
echo "$RANDOM" | tee "$outdir/x/random.txt" "$outdir/x/y/z/random.json"

find "$outdir" -type f -print0 | xargs -0 head
