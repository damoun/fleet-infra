terraform {
  cloud {
    organization = "damoun"
    workspaces {
      name = "fleet-infra-cloudflare"
    }
  }

  required_providers {
    random = {
      source = "hashicorp/random"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "4.26"
    }
  }
}
