data "terraform_remote_state" "hetzner" {
  backend = "local"

  config = {
    path = "../hetzner/terraform.tfstate"
  }
}

locals {
  load_balancer_ip  = data.terraform_remote_state.hetzner.outputs.load_balancer_ip
  control_plane_ips = data.terraform_remote_state.hetzner.outputs.control_plane_ips
  worker_ips        = data.terraform_remote_state.hetzner.outputs.worker_ips
}

resource "talos_machine_secrets" "this" {}

data "talos_machine_configuration" "control_plane" {
  cluster_name       = var.cluster_name
  machine_type       = "controlplane"
  cluster_endpoint   = "https://${local.load_balancer_ip}:6443"
  machine_secrets    = talos_machine_secrets.this.machine_secrets
  kubernetes_version = var.kubernetes_version

  config_patches = [
    yamlencode({
      cluster = {
        network = {
          cni = { name = "none" }
          podSubnets     = [var.pod_cidr]
          serviceSubnets = [var.service_cidr]
        }
        proxy = { disabled = true }
        etcd = {
          advertisedSubnets = [var.network_cidr]
        }
      }
      machine = {
        time = {
          servers = ["ntp1.hetzner.de", "ntp2.hetzner.com", "ntp3.hetzner.net"]
        }
        network = {
          nameservers = ["185.12.64.1", "185.12.64.2"]
          kubespan = {
            enabled = false
          }
        }
        features = {
          kubePrism = {
            enabled = true
            port    = 7445
          }
        }
        kubelet = {
          nodeIP = {
            validSubnets = [var.network_cidr]
          }
        }
      }
    }),
  ]
}

data "talos_machine_configuration" "worker" {
  cluster_name       = var.cluster_name
  machine_type       = "worker"
  cluster_endpoint   = "https://${local.load_balancer_ip}:6443"
  machine_secrets    = talos_machine_secrets.this.machine_secrets
  kubernetes_version = var.kubernetes_version

  config_patches = [
    yamlencode({
      cluster = {
        network = {
          cni = { name = "none" }
          podSubnets     = [var.pod_cidr]
          serviceSubnets = [var.service_cidr]
        }
        proxy = { disabled = true }
      }
      machine = {
        time = {
          servers = ["ntp1.hetzner.de", "ntp2.hetzner.com", "ntp3.hetzner.net"]
        }
        network = {
          nameservers = ["185.12.64.1", "185.12.64.2"]
          kubespan = {
            enabled = false
          }
        }
        features = {
          kubePrism = {
            enabled = true
            port    = 7445
          }
        }
        kubelet = {
          nodeIP = {
            validSubnets = [var.network_cidr]
          }
        }
      }
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
