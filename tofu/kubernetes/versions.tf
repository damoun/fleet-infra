terraform {
  required_version = "1.16.6"

  required_providers {
    kubernetes = {
      source  = "registry.opentofu.org/hashicorp/kubernetes"
      version = "2.38.0"
    }
  }
}
