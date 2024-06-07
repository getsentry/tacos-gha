#!/bin/bash
# Rename unzipped artifact files to something less surprising.
#
#   before: a⧸b⧸c  (key=10)
#   after: a/b/c/key=10
set -euo pipefail

src="$1"
dst="$(
  "$HERE/"ghadecode <<<"$(basename "$src")" |
    # FIXME: this should really be python (rename-tmp-dirs.sh)
    sed -r 's@^([^(]*) \((.*)\)$@\1/\2@'
)"

indir="$(dirname "$dst")/matrix-fan-in"
mkdir -p "$indir"
mv "$src" "$dst"

# fan-in metadata is made from the concatenated fan-out metadata:
outdir="$dst/matrix-fan-out"
find "$outdir" -mindepth 1 -maxdepth 1 -type f -print0 |
  xargs -r0 -n1 "$HERE/"append-to-dir "$indir" \
;
