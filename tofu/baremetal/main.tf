locals {
  control_plane_ips = [for k, v in var.control_plane_nodes : v.ip]
  worker_ips        = [for k, v in var.worker_nodes : v.ip]
  all_node_ips      = concat(local.control_plane_ips, local.worker_ips)

  common_machine_patch = {
    time = {
      servers = var.ntp_servers
    }
    network = {
      nameservers = var.dns_nameservers
      kubespan    = { enabled = false }
    }
    features = {
      kubePrism = { enabled = true, port = 7445 }
    }
    sysctls = {
      "fs.inotify.max_user_watches"   = "1048576"
      "fs.inotify.max_user_instances" = "8192"
      "vm.max_map_count"              = "524288"
    }
    kubelet = {
      nodeIP = { validSubnets = [var.vlan_cidr] }
      extraConfig = {
        shutdownGracePeriod         = "30s"
        shutdownGracePeriodCritical = "10s"
      }
    }
    install = {
      diskSelector = {
        type = "ssd"
      }
    }
    systemDiskEncryption = {
      state = {
        provider = "luks2"
        keys = [
          {
            nodeID = {}
            slot   = 0
          }
        ]
      }
      ephemeral = {
        provider = "luks2"
        keys = [
          {
            nodeID = {}
            slot   = 0
          }
        ]
      }
    }
  }

  common_cluster_patch = {
    network = {
      cni            = { name = "none" }
      podSubnets     = [var.pod_cidr]
      serviceSubnets = [var.service_cidr]
    }
    proxy = { disabled = true }
    apiServer = {
      certSANs = distinct(concat(
        [var.cluster_vip, var.netbird_domain],
        local.all_node_ips
      ))
    }
  }
}

resource "talos_machine_secrets" "this" {}

data "talos_machine_configuration" "control_plane" {
  for_each = var.control_plane_nodes

  cluster_name       = var.cluster_name
  machine_type       = "controlplane"
  cluster_endpoint   = "https://${var.cluster_vip}:6443"
  machine_secrets    = talos_machine_secrets.this.machine_secrets
  kubernetes_version = var.kubernetes_version

  config_patches = [
    yamlencode({
      machine = merge(local.common_machine_patch, {
        network = merge(local.common_machine_patch.network, {
          hostname = each.value.hostname
          interfaces = [
            {
              interface = var.cluster_vip_interface
              dhcp      = true
              vip = {
                ip = var.cluster_vip
              }
            }
          ]
        })
      })
      cluster = merge(local.common_cluster_patch, {
        etcd = { advertisedSubnets = [var.vlan_cidr] }
      })
    })
  ]
}

data "talos_machine_configuration" "worker" {
  for_each = var.worker_nodes

  cluster_name       = var.cluster_name
  machine_type       = "worker"
  cluster_endpoint   = "https://${var.cluster_vip}:6443"
  machine_secrets    = talos_machine_secrets.this.machine_secrets
  kubernetes_version = var.kubernetes_version

  config_patches = [
    yamlencode({
      machine = merge(local.common_machine_patch, {
        network = merge(local.common_machine_patch.network, {
          hostname = each.value.hostname
        })
      })
      cluster = local.common_cluster_patch
    })
  ]
}

resource "talos_machine_configuration_apply" "control_plane" {
  for_each = var.control_plane_nodes

  client_configuration        = talos_machine_secrets.this.client_configuration
  machine_configuration_input = data.talos_machine_configuration.control_plane[each.key].machine_configuration
  node                        = each.value.ip
}

resource "talos_machine_configuration_apply" "worker" {
  for_each = var.worker_nodes

  client_configuration        = talos_machine_secrets.this.client_configuration
  machine_configuration_input = data.talos_machine_configuration.worker[each.key].machine_configuration
  node                        = each.value.ip
}

resource "talos_machine_bootstrap" "this" {
  client_configuration = talos_machine_secrets.this.client_configuration
  node                 = var.control_plane_nodes["cp-vdcj"].ip

  depends_on = [talos_machine_configuration_apply.control_plane]
}

resource "talos_cluster_kubeconfig" "this" {
  client_configuration = talos_machine_secrets.this.client_configuration
  node                 = var.control_plane_nodes["cp-vdcj"].ip

  depends_on = [talos_machine_bootstrap.this]
}

data "talos_client_configuration" "this" {
  cluster_name         = var.cluster_name
  client_configuration = talos_machine_secrets.this.client_configuration
  nodes                = local.all_node_ips
  endpoints            = [var.cluster_vip]
}
