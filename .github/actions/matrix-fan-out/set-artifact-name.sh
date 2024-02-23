#!/bin/bash
# set the "artifact_name" step output

set -euo pipefail
# note: stdout goes to GITHUB_ENV
HERE="$GITHUB_ACTION_PATH"

path="$1"

set -x
: Calculate artifact name
(
  echo "artifact_name="
  # remove any leading ./
  sed -r 's@^\./+@@g' <<<"$path"
) |
  tr -d '\n' |
  "$HERE/"ghaencode \
;
