terraform {
  required_version = "1.17.1"

  required_providers {
    kubernetes = {
      source  = "registry.opentofu.org/hashicorp/kubernetes"
      version = "3.4.0"
    }
  }
}
