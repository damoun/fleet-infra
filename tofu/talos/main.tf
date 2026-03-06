data "terraform_remote_state" "hetzner" {
  backend = "local"

  config = {
    path = "../hetzner/terraform.tfstate"
  }
}

locals {
  control_plane_ips = data.terraform_remote_state.hetzner.outputs.control_plane_ips
  worker_ips        = data.terraform_remote_state.hetzner.outputs.worker_ips
}

resource "talos_machine_secrets" "this" {}

locals {
  common_machine_patch = {
    time = {
      servers = ["ntp1.hetzner.de", "ntp2.hetzner.com", "ntp3.hetzner.net"]
    }
    network = {
      nameservers = ["185.12.64.1", "185.12.64.2"]
      kubespan    = { enabled = false }
    }
    features = {
      kubePrism = { enabled = true, port = 7445 }
    }
    kubelet = {
      nodeIP = { validSubnets = [var.network_cidr] }
    }
  }

  common_cluster_patch = {
    network = {
      cni            = { name = "none" }
      podSubnets     = [var.pod_cidr]
      serviceSubnets = [var.service_cidr]
    }
    proxy = { disabled = true }
  }
}

data "talos_machine_configuration" "control_plane" {
  cluster_name       = var.cluster_name
  machine_type       = "controlplane"
  cluster_endpoint   = "https://${local.control_plane_ips[0]}:6443"
  machine_secrets    = talos_machine_secrets.this.machine_secrets
  kubernetes_version = var.kubernetes_version

  config_patches = [
    yamlencode({
      cluster = merge(local.common_cluster_patch, {
        etcd = { advertisedSubnets = [var.node_subnet_cidr] }
      })
      machine = local.common_machine_patch
    }),
  ]
}

data "talos_machine_configuration" "worker" {
  cluster_name       = var.cluster_name
  machine_type       = "worker"
  cluster_endpoint   = "https://${local.control_plane_ips[0]}:6443"
  machine_secrets    = talos_machine_secrets.this.machine_secrets
  kubernetes_version = var.kubernetes_version

  config_patches = [
    yamlencode({
      cluster = local.common_cluster_patch
      machine = local.common_machine_patch
    }),
  ]
}

resource "talos_machine_configuration_apply" "control_plane" {
  count                       = length(local.control_plane_ips)
  client_configuration        = talos_machine_secrets.this.client_configuration
  machine_configuration_input = data.talos_machine_configuration.control_plane.machine_configuration
  node                        = local.control_plane_ips[count.index]
}

resource "talos_machine_configuration_apply" "worker" {
  count                       = length(local.worker_ips)
  client_configuration        = talos_machine_secrets.this.client_configuration
  machine_configuration_input = data.talos_machine_configuration.worker.machine_configuration
  node                        = local.worker_ips[count.index]
}

resource "talos_machine_bootstrap" "this" {
  client_configuration = talos_machine_secrets.this.client_configuration
  node                 = local.control_plane_ips[0]

  depends_on = [talos_machine_configuration_apply.control_plane]
}

resource "talos_cluster_kubeconfig" "this" {
  client_configuration = talos_machine_secrets.this.client_configuration
  node                 = local.control_plane_ips[0]

  depends_on = [talos_machine_bootstrap.this]
}

data "talos_client_configuration" "this" {
  cluster_name         = var.cluster_name
  client_configuration = talos_machine_secrets.this.client_configuration
  nodes                = concat(local.control_plane_ips, local.worker_ips)
  endpoints            = local.control_plane_ips
}
