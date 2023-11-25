terraform {
  cloud {
    organization = "damoun"
    workspaces {
      name = "fleet-infra-tfe"
    }
  }

  required_providers {
    tfe = {
      source  = "hashicorp/tfe"
      version = "0.50.0"
    }
  }
}
