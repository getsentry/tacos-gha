#!/bin/bash
# Set artifact_name output, but also ensure matrix context appears at fan-in.

set -euo pipefail
# note: stdout goes to GITHUB_ENV
HERE="$GITHUB_ACTION_PATH"

matrix="$(
  jq \
    <<<"$GHA_MATRIX_CONTEXT" \
    'to_entries | sort | map("\(.key)=\(.value)") | join("/")' \
    --raw-output \
  ;
)"

cat >&2 <<EOF
## prepare.sh: record metadata
gha-matrix-context.json:

$GHA_MATRIX_CONTEXT

matrix.list:

$matrix

EOF

find . -type d -path "$MATRIX_FAN_OUT_PATH" -print0 |
  if ! grep -z .; then
    echo >&2 "No fan-out directories found: $MATRIX_FAN_OUT_PATH"
    exit 1
  fi |
  while IFS= read -rd '' outdir; do
    cat > "$outdir/"gha-matrix-context.json <<<"$GHA_MATRIX_CONTEXT"
    cat > "$outdir/"matrix.list <<<"$matrix"
  done \
;

: Calculate artifact name
"$HERE/"set-artifact-name.sh "$MATRIX_FAN_OUT_PATH/($matrix)"
