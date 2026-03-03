terraform {
  required_version = ">= 1.11"

  required_providers {
    hcloud = {
      source  = "registry.opentofu.org/hetznercloud/hcloud"
      version = "~> 1.60"
    }
    talos = {
      source  = "registry.opentofu.org/siderolabs/talos"
      version = "0.11.0-beta.1"
    }
  }
}

provider "hcloud" {
  token = var.hcloud_token
}

provider "talos" {}
