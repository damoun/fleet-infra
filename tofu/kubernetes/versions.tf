terraform {
  required_version = ">= 1.11"

  required_providers {
    kubernetes = {
      source  = "registry.opentofu.org/hashicorp/kubernetes"
      version = "~> 2.36"
    }
  }
}
