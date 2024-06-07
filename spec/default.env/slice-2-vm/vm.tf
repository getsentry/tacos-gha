variable "deploy_env" {
  type = string
}

resource "random_uuid" "disk_id" {
}

resource "null_resource" "vm" {
  triggers = {
    name    = "${var.deploy_env}-vm-1"
    disk_id = random_uuid.disk_id.result
  }
}
