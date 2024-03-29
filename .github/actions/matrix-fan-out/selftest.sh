#!/bin/bash
# This script represents a "worst case" (but valid) use case.
# Send more than one json to fan-in, as well as some auxilliary data, via a
# non-default path.

set -euo pipefail
exec >&2  # our only output is logging
HERE="$(readlink -f "$(dirname "$0")")"

key="$1"

set -x

: Processing... "$key"
outdir="a/b/c"
mkdir -p "$outdir/x/y/z"

echo "$key" > "$outdir/key"
echo 1 > "$outdir/x/y/matrix.1.json"
"$HERE/"square.py "$key" > "$outdir/"square.txt

square=$((key ** 2))
echo "$square" | tee "$outdir/square" "$outdir/x/y/z/matrix.json"
echo "$RANDOM" | tee "$outdir/x/random.txt" "$outdir/x/y/z/random.json"

outdir="a/b/c"
find "$outdir" -type f -print0 | xargs -0 head
