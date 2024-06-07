locals {
  default_config = { inputs = {} }
  env_vars = read_terragrunt_config(
    find_in_parent_folders("project.hcl"),
    local.default_config,
  )
}

inputs = merge(
  local.env_vars.inputs
)

generate "_backend.tf" {
  path      = "_backend.tf"
  if_exists = "overwrite"
  contents  = <<EOF
terraform {
  backend "gcs" {
    bucket   = "sac-dev-tf--tacos-gha"
    prefix   = "tacos-demo/${path_relative_to_include()}"
  }
}
EOF
}

# https://terragrunt.gruntwork.io/docs/features/auto-retry/
retryable_errors = [
  # a 2-10% flake that seems to be caused by:
  #   https://github.com/hashicorp/terraform/blob/main/internal/providercache/installer.go#L296-L306
  "(?s).*Failed to query available provider packages.*INTERNAL_ERROR; received from peer.*",

  # default values:  https://terragrunt.gruntwork.io/docs/reference/config-blocks-and-attributes/#retryable_errors
  "(?s).*Failed to load state.*tcp.*timeout.*",
  "(?s).*Failed to load backend.*TLS handshake timeout.*",
  "(?s).*Creating metric alarm failed.*request to update this alarm is in progress.*",
  "(?s).*Error installing provider.*TLS handshake timeout.*",
  "(?s).*Error configuring the backend.*TLS handshake timeout.*",
  "(?s).*Error installing provider.*tcp.*timeout.*",
  "(?s).*Error installing provider.*tcp.*connection reset by peer.*",
  #"NoSuchBucket: The specified bucket does not exist",
  "(?s).*Error creating SSM parameter: TooManyUpdates:.*",
  "(?s).*app.terraform.io.*: 429 Too Many Requests.*",
  "(?s).*ssh_exchange_identification.*Connection closed by remote host.*",
  "(?s).*Client\\.Timeout exceeded while awaiting headers.*",
  "(?s).*Could not download module.*The requested URL returned error: 429.*",
]
