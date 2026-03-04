data "terraform_remote_state" "talos" {
  backend = "local"

  config = {
    path = "../talos/terraform.tfstate"
  }
}

locals {
  kubeconfig = yamldecode(data.terraform_remote_state.talos.outputs.kubeconfig)
}

provider "kubernetes" {
  host                   = local.kubeconfig.clusters[0].cluster.server
  client_certificate     = base64decode(local.kubeconfig.users[0].user.client-certificate-data)
  client_key             = base64decode(local.kubeconfig.users[0].user.client-key-data)
  cluster_ca_certificate = base64decode(local.kubeconfig.clusters[0].cluster.certificate-authority-data)
}

resource "kubernetes_namespace" "flux_system" {
  metadata {
    name = "flux-system"
  }

  lifecycle {
    ignore_changes = [metadata[0].labels, metadata[0].annotations]
  }
}

resource "kubernetes_namespace" "netbird" {
  metadata {
    name = "netbird"
  }
}

resource "kubernetes_secret" "sops_age" {
  metadata {
    name      = "sops-age"
    namespace = kubernetes_namespace.flux_system.metadata[0].name
  }

  data = {
    "age.agekey" = var.sops_age_key
  }
}

resource "kubernetes_secret" "hcloud" {
  metadata {
    name      = "hcloud"
    namespace = "kube-system"
  }

  data = {
    token = var.hcloud_token
  }
}
