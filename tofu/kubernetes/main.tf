data "terraform_remote_state" "talos" {
  backend = "local"

  config = {
    path = "../talos/terraform.tfstate"
  }
}

data "terraform_remote_state" "netbird" {
  backend = "local"

  config = {
    path = "../netbird/terraform.tfstate"
  }
}

provider "kubernetes" {
  config_path = null
  host        = yamldecode(data.terraform_remote_state.talos.outputs.kubeconfig).clusters[0].cluster.server

  client_certificate     = base64decode(yamldecode(data.terraform_remote_state.talos.outputs.kubeconfig).users[0].user.client-certificate-data)
  client_key             = base64decode(yamldecode(data.terraform_remote_state.talos.outputs.kubeconfig).users[0].user.client-key-data)
  cluster_ca_certificate = base64decode(yamldecode(data.terraform_remote_state.talos.outputs.kubeconfig).clusters[0].cluster.certificate-authority-data)
}

resource "kubernetes_namespace" "netbird" {
  metadata {
    name = "netbird"
  }
}

resource "kubernetes_secret" "sops_age" {
  metadata {
    name      = "sops-age"
    namespace = "flux-system"
  }

  data = {
    "age.agekey" = var.sops_age_key
  }
}

resource "kubernetes_secret" "netbird_setup_key" {
  metadata {
    name      = "netbird-setup-key"
    namespace = kubernetes_namespace.netbird.metadata[0].name
  }

  data = {
    setupKey = data.terraform_remote_state.netbird.outputs.setup_key
  }
}
