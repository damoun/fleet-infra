terraform {
  required_version = "1.15.0"

  required_providers {
    talos = {
      source  = "registry.opentofu.org/siderolabs/talos"
      version = "0.11.0-beta.2"
    }
  }
}

provider "talos" {}
