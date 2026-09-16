terraform {
  required_version = "1.16.2"

  required_providers {
    talos = {
      source  = "registry.opentofu.org/siderolabs/talos"
      version = "0.11.0"
    }
  }
}

provider "talos" {}
