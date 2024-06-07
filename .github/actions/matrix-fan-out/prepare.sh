#!/bin/bash
# Set artifact_name output, but also ensure matrix context appears at fan-in.

set -euo pipefail
# note: stdout goes to GITHUB_ENV
HERE="$GITHUB_ACTION_PATH"
outdir="matrix-fan-out"

matrix="$(
  jq \
    <<<"$GHA_MATRIX_CONTEXT" \
    'to_entries | sort | map("\(.key)=\(.value)") | join("/")' \
    --raw-output \
  ;
)"

set -x
mkdir -p "$outdir"

: Record matrix context
tee >&2 <<< "$GHA_MATRIX_CONTEXT" "$outdir/context.json"
tee >&2 <<< "$matrix" "$outdir/matrix.list"

( { set -e +x ; } 2>/dev/null
  find . \
    \( -not -user "$USER" -prune \) -or \
    \( -type d -path "$MATRIX_FAN_OUT_PATH" -print0 -prune \) |
  sed -z 's/^\.\///' |  # snip silly leading ./
  xargs -r0 -n1 sh -c 'echo "$1/$2"' - "$matrix"
) |
  tee >&2 "$outdir/path.list" \
;

: Calculate artifact name
"$HERE/"set-artifact-name.sh "$MATRIX_FAN_OUT_PATH ($matrix)"
