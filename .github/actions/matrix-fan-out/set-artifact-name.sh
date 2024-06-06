#!/bin/bash
# set the "artifact_name" step output

set -euo pipefail
# note: stdout goes to GITHUB_ENV
HERE="$GITHUB_ACTION_PATH"

path="$1"

set -x
: Calculate artifact name
echo -n "artifact_name="
"$HERE/"ghaencode <<< "$path"
