#!/bin/bash
# final step of fan-in: rename tmp dirs to something less suprising
#
#   before: ./matrix-fan-in.tmp/a b c (key=10)
#   after: a/b/c/key=10

set -euo pipefail
exec >&2  # our only output is logging
export HERE="$GITHUB_ACTION_PATH"

set -x
path="$1"

mkdir -p "$path"

# Fail early if no artifacts were downloaded
if [ ! -d ./matrix-fan-in.tmp ] || [ -z "$(ls -A ./matrix-fan-in.tmp 2>/dev/null)" ]; then
  echo "ERROR: No artifacts found in matrix-fan-in.tmp" >&2
  echo "This may indicate matrix jobs failed or we touched too many slices and exceeded Github's 256 matrix limit." >&2
  exit 1
fi

: directory name fixup
find ./matrix-fan-in.tmp \
    -mindepth 1 \
    -maxdepth 1 \
    -print0 \
  |
  xargs -0 -r -n1 "$HERE/"rename-tmp-dir.sh \
> "$path/matrix.list"

: assertion: the directory is empty
rmdir matrix-fan-in.tmp

: now lets us have a looksee, shall we?
tree -Chap --metafirst "$path" || : code $?

tail -vn99 "$path/"matrix.list
