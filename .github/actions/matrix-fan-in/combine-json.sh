#!/bin/bash
# final step of fan-in: find and combine the matrix-shards' json outputs

set -euo pipefail
exec >&2  # our only output is logging
export HERE="$GITHUB_ACTION_PATH"

set -x
path="$1"
files="$2"

: directory name fixup
find ./matrix-fan-in.tmp \
    -mindepth 1 \
    -maxdepth 1 \
    -print0 |
  xargs -0 -n1 "$HERE/"rename-tmp.sh \
;

: assertion: the directory is empty
rmdir matrix-fan-in.tmp

: now lets have a looksee
namei -l "$path" || : code $?
find "$path" -type f -print0 | xargs -0 ls -lh || : code $?

cd "$path"
find . -name "$files" -print0 |
  sort -z |
  xargs -0 --replace \
    jq --arg filename {} '{ ($filename): . }' {} |
  jq -s add |
  tee matrix.json \
;
