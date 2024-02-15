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
  echo "matrix/"
  # remove any leading ./
  sed -r 's@^\./+@@g' <<<"$path"
  cat  # send extra path components on stdin
) |
  tr -d '\n' |
  "$HERE/"ghaencode \
;
