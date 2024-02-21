#!/bin/bash
# Rename unzipped artifact files to something less surprising.
#
#   before: ./matrix-fan-in.tmp/matrix a b c (key=10)
#   after: a/b/c/key=10

set -euo pipefail
exec >&2  # our only output is logging

tmpfile="$1"
newfile="$(
  "$HERE/"ghadecode <<<"$tmpfile" |
    # FIXME: matrix-fan-in/rename-tmp should really be python
    sed -r 's@^\./matrix-fan-in\.tmp/([^(]*/)\((.*)\)$@\1\2@'
)"
parent="$(dirname "$newfile")"

set -x
: tmpfile: "$tmpfile"
mkdir -p "$parent"
mv -v "$tmpfile" "$newfile"
