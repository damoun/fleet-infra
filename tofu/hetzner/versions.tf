terraform {
  required_version = "1.15.1"

  required_providers {
    hcloud = {
      source  = "registry.opentofu.org/hetznercloud/hcloud"
      version = "1.62.0"
    }
  }
}

provider "hcloud" {
  token = var.hcloud_token
}
