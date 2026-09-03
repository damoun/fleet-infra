terraform {
  required_version = ">= 1.11.0"

  required_providers {
    hcloud = {
      source  = "registry.opentofu.org/hetznercloud/hcloud"
      version = "1.68.0"
    }
  }
}

provider "hcloud" {
  token = var.hcloud_token
}
