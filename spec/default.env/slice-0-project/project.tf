variable "project" {
  type = string
}

resource "null_resource" "project" {
  triggers = {
    project = var.project
  }
}
