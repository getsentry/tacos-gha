#!/bin/bash
# delete all but the last terraform-plan PR comment
set -euo pipefail
HERE="$(cd "$(dirname "$0")"; pwd)"

gh pr view --json comments |
  jq --raw-output '
  ( .comments
  | map(
      select(
        .body
      | startswith("<details>\n<summary>Execution result of \"run-all plan\" in \".\"" )
      )
    | .id
    )
  | .[:-1].[]
  )' |

  xargs -I{} \
    gh api graphql \
      -F 'id={}' \
      -F classifier=OUTDATED \
      -f query="$(cat "$HERE/"delete-comment.graphql)" \
    \
  \
;
