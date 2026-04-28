terraform {
  required_version = "1.14.9"

  required_providers {
    talos = {
      source  = "registry.opentofu.org/siderolabs/talos"
      version = "0.11.0-beta.1"
    }
  }
}

provider "talos" {}
