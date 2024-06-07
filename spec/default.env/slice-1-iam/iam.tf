variable "project" {
  type = string
}

resource "null_resource" "iam-policy" {
  triggers = {
    project = var.project
    policy = jsonencode({
      role = "roles/owner"
      members = [
        "me@example.com",
        "you@example.com",
      ]
    })
  }
}
