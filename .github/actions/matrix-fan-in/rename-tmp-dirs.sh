#!/bin/bash
# final step of fan-in: rename tmp dirs to something less suprising
#
#   before: ./matrix-fan-in.tmp/a b c (key=10)
#   after: a/b/c/key=10

set -euo pipefail
exec >&2  # our only output is logging
export artifact_name  # set by prior step
export HERE="$GITHUB_ACTION_PATH"

set -x
path="$1"
indir="$path/matrix-fan-in"

mkdir -p "$indir"

: directory name fixup
find ./matrix-fan-in.tmp \
    -mindepth 1 \
    -maxdepth 1 \
    -print0 \
  |
  xargs -0 -n1 "$HERE/"rename-tmp-dir.sh |
tee "$indir/path.list"

cat < "$indir/path.list" |
  xargs --replace cat "{}/matrix-fan-out/context.json" |
tee "$indir/context.json"

: assertion: the tmp directory is empty
rmdir matrix-fan-in.tmp

: now lets us have a looksee, shall we?
tree -Chap --metafirst "$path" || : code $?

tail -vn99 "$path/"matrix-fan-in/path.list
