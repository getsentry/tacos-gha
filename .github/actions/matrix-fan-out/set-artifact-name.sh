#!/bin/bash
# set the "artifact_name" step output

set -euo pipefail
# note: stdout goes to GITHUB_OUTPUT
HERE="$GITHUB_ACTION_PATH"

path="$1"

: Calculate artifact name
artifact=$(
  sed <<< "$path" 's/^\.\///' |  # snip silly leading ./
  "$HERE/"ghaencode
)
echo "artifact=$artifact"
