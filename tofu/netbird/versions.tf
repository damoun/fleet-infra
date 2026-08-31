terraform {
  required_providers {
    netbird = {
      source  = "netbirdio/netbird"
      version = "0.0.10"
    }
  }
}

provider "netbird" {
  token = var.netbird_token
}
