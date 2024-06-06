#!/bin/bash
# Rename unzipped artifact files to something less surprising.
#
#   before: a⧸b⧸c⧸(key=10)
#   after: a/b/c/key=10
set -euo pipefail

tmpfile="$1"
newfile="$(
  "$HERE/"ghadecode <<<"$tmpfile" |
    # FIXME: matrix-fan-in/rename-tmp should really be python
    sed -r 's@^\./matrix-fan-in\.tmp/([^(]*/)\((.*)\)$@\1\2@'
)"
parent="$(dirname "$newfile")"
key="$(basename "$newfile")"

mkdir -p "$parent"
mv "$tmpfile" "$newfile"

# note stdout becomes matrix-fan-in/path.list
echo -n "$key/"
cat "$newfile/matrix-fan-out/path.list"
