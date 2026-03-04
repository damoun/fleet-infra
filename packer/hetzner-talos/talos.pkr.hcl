packer {
  required_plugins {
    hcloud = {
      source  = "github.com/hetznercloud/hcloud"
      version = "~> 1"
    }
  }
}

variable "hcloud_token" {
  type      = string
  sensitive = true
}

variable "talos_version" {
  type    = string
  default = "v1.12.4"
}

variable "location" {
  type    = string
  default = "fsn1"
}

locals {
  image_url = "https://factory.talos.dev/image/ce4c980550dd2ab1b17bbf2b08801c7eb59418eafe8f279833297925d67c7515/${var.talos_version}/hcloud-amd64.raw.xz"
}

source "hcloud" "talos" {
  token        = var.hcloud_token
  location     = var.location
  server_type  = "cx22"
  image        = "debian-12"
  rescue       = "linux64"
  ssh_username = "root"
  snapshot_labels = {
    type    = "talos"
    version = var.talos_version
  }
  snapshot_name = "talos-${var.talos_version}"
}

build {
  sources = ["source.hcloud.talos"]

  provisioner "shell" {
    inline = [
      "apt-get install -y wget xz-utils",
      "wget -q -O /tmp/talos.raw.xz '${local.image_url}'",
      "xz -d /tmp/talos.raw.xz",
      "dd if=/tmp/talos.raw of=/dev/sda bs=4M status=progress",
      "sync",
    ]
  }
}
