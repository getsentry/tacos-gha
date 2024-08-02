#!/bin/bash
# Set artifact_name output, but also ensure matrix context appears at fan-in.

set -euo pipefail
# note: stdout goes to GITHUB_ENV
HERE="$GITHUB_ACTION_PATH"

set -x

: Record matrix context
mkdir -p "$MATRIX_FAN_OUT_PATH"
tee \
  <<<"$GHA_MATRIX_CONTEXT" \
  "$MATRIX_FAN_OUT_PATH/gha-matrix-context.json" \
  >&2 \
;

matrix="$(
  jq \
    <<<"$GHA_MATRIX_CONTEXT" \
    'to_entries | sort | map("\(.key)=\(.value)") | join("/")' \
    --raw-output \
  ;
)"

tee "$MATRIX_FAN_OUT_PATH"/matrix.list <<< "$matrix"

: Calculate artifact name
"$HERE/"set-artifact-name.sh "$MATRIX_FAN_OUT_PATH/($matrix)"
