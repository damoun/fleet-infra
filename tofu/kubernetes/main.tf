data "terraform_remote_state" "baremetal" {
  backend = "local"

  config = {
    path = "../baremetal/terraform.tfstate"
  }
}

locals {
  kubeconfig = yamldecode(data.terraform_remote_state.baremetal.outputs.kubeconfig)
}

provider "kubernetes" {
  host                   = local.kubeconfig.clusters[0].cluster.server
  client_certificate     = base64decode(local.kubeconfig.users[0].user.client-certificate-data)
  client_key             = base64decode(local.kubeconfig.users[0].user.client-key-data)
  cluster_ca_certificate = base64decode(local.kubeconfig.clusters[0].cluster.certificate-authority-data)
}

resource "kubernetes_namespace_v1" "flux_system" {
  metadata {
    name = "flux-system"
  }

  lifecycle {
    ignore_changes = [metadata[0].labels, metadata[0].annotations]
  }
}

resource "kubernetes_secret_v1" "sops_age" {
  metadata {
    name      = "sops-age"
    namespace = kubernetes_namespace_v1.flux_system.metadata[0].name
  }

  data = {
    "age.agekey" = var.sops_age_key
  }
}
