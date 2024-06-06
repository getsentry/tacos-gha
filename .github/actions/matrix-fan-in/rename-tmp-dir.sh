#!/bin/bash
# Rename unzipped artifact files to something less surprising.
#
#   before: a⧸b⧸c⧸(key=10)
#   after: a/b/c/key=10
set -euo pipefail
# note stdout becomes matrix.list

tmpfile="$1"
newfile="$(
  "$HERE/"ghadecode <<<"$tmpfile" |
    # FIXME: matrix-fan-in/rename-tmp should really be python
    sed -r 's@^\./matrix-fan-in\.tmp/([^(]*/)\((.*)\)$@\1\2@'
)"
parent="$(dirname "$newfile")"

mkdir -p "$parent"
mv "$tmpfile" "$newfile"
cat "$newfile/matrix.list"
