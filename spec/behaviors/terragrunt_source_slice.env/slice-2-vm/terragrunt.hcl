dependencies {
  paths = ["../slice-0-project", "../slice-1-iam"]
}

include "base" {
  path = find_in_parent_folders("terragrunt-base.hcl")
}

terraform {
  source = "../module/slice-2-vm"
}
