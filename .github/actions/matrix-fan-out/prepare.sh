#!/bin/bash
# Set artifact_name output, but also ensure matrix context appears at fan-in.

set -euo pipefail
# note: stdout goes to GITHUB_ENV
HERE="$GITHUB_ACTION_PATH"

set -x

: Record matrix context
tee \
  <<<"$MATRIX_FAN_OUT_CONTEXT" \
  "$MATRIX_FAN_OUT_PATH/gha-matrix-context.json" \
  >&2 \
;

: Calculate artifact name
(
  echo '/('
  jq \
    <<<"$MATRIX_FAN_OUT_CONTEXT" \
    'to_entries | sort | map("\(.key)=\(.value)") | join("/")' \
    --raw-output \
  ;
  echo ')'
) |
  "$HERE/"artifact-name.sh "$MATRIX_FAN_OUT_PATH" \
;
