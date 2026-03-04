terraform {
  required_version = ">= 1.11"

  required_providers {
    netbird = {
      source  = "registry.opentofu.org/netbirdio/netbird"
      version = "~> 0.0.8"
    }
  }
}

provider "netbird" {
  token = var.netbird_api_token
}
