terraform {
  required_version = "1.15.9"

  required_providers {
    kubernetes = {
      source  = "registry.opentofu.org/hashicorp/kubernetes"
      version = "v3.2.1"
    }
  }
}
