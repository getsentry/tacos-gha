#!/bin/bash
# final step of fan-in: rename tmp dirs to something less suprising
#
#   before: ./matrix-fan-in.tmp/a b c (key=10)
#   after: a/b/c/key=10

set -euo pipefail
exec >&2  # our only output is logging
export HERE="$GITHUB_ACTION_PATH"

set -x

: directory name fixup
find "$MATRIX_TMP" \
    -mindepth 1 \
    -maxdepth 1 \
    -print0 \
  |
  xargs -r0 -n1 "$HERE/"rename-tmp-dir.sh \
;

: assertion: the tmp directory is empty
rmdir "$MATRIX_TMP"

: now lets us have a looksee, shall we?
tree -Chap --metafirst "$MATRIX_FAN_OUT_PATH"
tail -vn99 "$MATRIX_FAN_OUT_PATH/"matrix-fan-in/*
