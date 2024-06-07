dependencies {
  paths = ["../slice-0-project"]
}

include "base" {
  path = find_in_parent_folders("terragrunt-base.hcl")
}

terraform {
  source = "../module/slice-1-iam"
}
