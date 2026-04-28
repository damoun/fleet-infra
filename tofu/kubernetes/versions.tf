terraform {
  required_version = "1.14.9"

  required_providers {
    kubernetes = {
      source  = "registry.opentofu.org/hashicorp/kubernetes"
      version = "2.38.0"
    }
  }
}
