#!/usr/bin/env -S jq -rf

( (env["TF_LOCK_ENONE"] | tonumber) as $TF_LOCK_ENONE
| if .ID != null
  then .ID
  else
    # terraform state not locked
    null | halt_error($TF_LOCK_ENONE)
  end
)
