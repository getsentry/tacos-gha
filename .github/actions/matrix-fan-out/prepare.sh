#!/bin/bash
# Set artifact_name output, but also ensure matrix context appears at fan-in.

set -euo pipefail
# note: stdout goes to GITHUB_ENV
HERE="$GITHUB_ACTION_PATH"
outdir="matrix-fan-out"

set -x
mkdir -p "$outdir"

: Record matrix context
mkdir -p "$MATRIX_FAN_OUT_PATH"
tee >&2 <<<"$GHA_MATRIX_CONTEXT" "$outdir/context.json"

matrix="$(
  jq \
    <<<"$GHA_MATRIX_CONTEXT" \
    'to_entries | sort | map("\(.key)=\(.value)") | join("/")' \
    --raw-output \
  ;
)"
find . -type d -path "$MATRIX_FAN_OUT_PATH" -print0 |
  sed -z 's/^\.\///' |  # snip silly leading ./
  xargs -r0 -n1 sh -c 'echo "$1/$2"' - "$matrix" |
  tee >&2 "$outdir/path.list" \
;
echo "$matrix" > "$outdir/matrix.list"

: Calculate artifact name
"$HERE/"set-artifact-name.sh "$MATRIX_FAN_OUT_PATH ($matrix)"
