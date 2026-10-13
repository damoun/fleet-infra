terraform {
  required_version = ">= 1.8.0"

  required_providers {
    talos = {
      source  = "registry.opentofu.org/siderolabs/talos"
      version = "~> 0.12.0"
    }
  }
}

provider "talos" {}
