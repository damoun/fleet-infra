terraform {
  cloud {
    organization = "damoun"
    workspaces {
      name = "fleet-infra-nas"
    }
  }

  required_providers {
    truenas = {
      source  = "dariusbakunas/truenas"
      version = "0.11.1"
    }
  }
}
