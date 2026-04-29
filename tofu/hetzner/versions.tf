terraform {
  required_version = "1.15.0"

  required_providers {
    hcloud = {
      source  = "registry.opentofu.org/hetznercloud/hcloud"
      version = "v1.62.0"
    }
  }
}

provider "hcloud" {
  token = var.hcloud_token
}
