terraform {
  required_version = "1.15.5"

  required_providers {
    kubernetes = {
      source  = "registry.opentofu.org/hashicorp/kubernetes"
      version = "v2.38.0"
    }
  }
}
