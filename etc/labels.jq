#!/usr/bin/env -S jq -nf
# Change this to yaml if you want; I just didn't want the extra dependency.

# github issue labels used by the TACOS-gha system

# initial data populated with:
# $ gh label list -R getsentry/tacos-gha.demo --json color,createdAt,description,id,isDefault,name,updatedAt,url | yq -P

# TACO color scheme: https://www.color-hex.com/color-palette/31032
#       plan taco     #f6c95c   (246,201,92)
#       lock queso    #e7af00   (231,175,0)
#   conflict salsa    #c91919   (201,25,25)
#     unlock lechuga  #41a332   (65,163,50)
#      apply carne    #983d00   (152,61,0)
#      stale taco mal #877958   (135, 121, 88)

( {
    "name": ":taco::lock",
    "description": "This PR holds a terraform state lock.",
    "color": "e7af00",
  }

, {
    "name": ":taco::conflict",
    "description": "TACOS has detected a merge conflict.",
    "color": "c91919",
  }

, {
    "name": ":taco::unlock",
    "description": "Release the terraform lock for these changes.",
    "color": "41a332",
  }

, {
    "name": ":taco::apply",
    "description": "Request a terraform apply of these changes.",
    "color": "983d00",
  }

, { "name": ":taco::plan",
    "description": "Request a terraform plan for these changes.",
    "color": "f6c95c",
  }

, {
    "name": ":taco::stale",
    "description": "This change has (perhaps) been abandoned.",
    "color": "FFFFFF",
  }
)
