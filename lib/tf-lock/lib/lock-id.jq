#!/usr/bin/env -S jq -rf
if .ID != null
then .ID
else
  # terraform state not locked
  null | halt_error(2)
end
