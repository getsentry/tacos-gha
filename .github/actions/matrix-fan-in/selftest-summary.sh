#!/bin/bash
set -euo pipefail
outdir="$1"

( cd "$outdir"
  echo '# squares'
  echo
  echo "Squares computed: ($(wc -l < matrix-fan-in/path.list) total)"
  xargs < matrix-fan-in/path.list --replace cat {}/key |
    sort -n |
    while IFS= read -r key; do
      echo "  * $key"
    done \
  ;

  sort -n matrix-fan-in/path.list |
    while read -r matrix; do
      key="$(cat "$matrix/key")"
      cat <<EOF
## $key squared
<!-- getsentry/tacos-gha "matrix-selftest($key)" -->

The square of $key is $(cat "$matrix/square")

\`\`\`
$(cat "$matrix/"square.txt)
\`\`\`

EOF

    done \
  ;

  cat <<EOF
## files archived

\`\`\`console
EOF

  ( set -x; tree ) 2>&1 |
    # transform xtrace logging to `console` syntax
    sed -r 's/^\++/\n$/' \
  ;
  echo '```'
) |
  tee -a \
    "$GITHUB_STEP_SUMMARY" \
    >(
      jq -sR |
      sed 's/^/summary=/' \
      >> "$GITHUB_OUTPUT"
    ) \
  \
;
