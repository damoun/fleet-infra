locals {
  control_plane_ips = [for k, v in var.control_plane_nodes : v.ip]
  worker_ips        = [for k, v in var.worker_nodes : v.ip]
  all_node_ips      = concat(local.control_plane_ips, local.worker_ips)

  # Base v1alpha1 machine patch (sysctls only; disk encryption lives in the VolumeConfig docs below)
  common_v1alpha1_machine_patch = {
    sysctls = {
      "fs.inotify.max_user_watches"   = "1048576"
      "fs.inotify.max_user_instances" = "8192"
      "vm.max_map_count"              = "524288"
    }
  }

  # LUKS2 + TPM key for the system volumes, bound to the signed PCR 11 (UKI) policy only.
  # PCR 7 is intentionally excluded so firmware/SecureBoot db(dbx) updates cannot make the
  # volume permanently unsealable. checkSecurebootStatusOnEnroll makes the install fail
  # loudly if SecureBoot is not actually enabled on the node.
  #
  # NOTE: Talos re-encodes an empty `pcrs` list as `options: {}` (omitempty), which is
  # equivalent - see TestVolumeConfigTPMPCRsDefaults in the Talos repo. Providing `options`
  # at all is what disables the default PCR 7 binding; omitting `options` would re-enable it.
  system_volume_tpm_key = {
    slot = 0
    tpm = {
      checkSecurebootStatusOnEnroll = true
      options = {
        pcrs = []
      }
    }
  }

  system_volume_patches_tpm = [
    yamlencode({
      apiVersion = "v1alpha1"
      kind       = "VolumeConfig"
      name       = "STATE"
      encryption = {
        provider = "luks2"
        keys     = [local.system_volume_tpm_key]
      }
    }),
    yamlencode({
      apiVersion = "v1alpha1"
      kind       = "VolumeConfig"
      name       = "EPHEMERAL"
      encryption = {
        provider = "luks2"
        keys     = [local.system_volume_tpm_key]
      }
    }),
  ]

  system_volume_patches_nodeid = [
    yamlencode({
      apiVersion = "v1alpha1"
      kind       = "VolumeConfig"
      name       = "STATE"
      encryption = {
        provider = "luks2"
        keys     = [{ slot = 0, nodeID = {} }]
      }
    }),
    yamlencode({
      apiVersion = "v1alpha1"
      kind       = "VolumeConfig"
      name       = "EPHEMERAL"
      encryption = {
        provider = "luks2"
        keys     = [{ slot = 0, nodeID = {} }]
      }
    }),
  ]

  # Both branches are list(string) so the conditional stays type-consistent
  # (differently-shaped key objects would otherwise trip "Inconsistent conditional
  # result types").
  system_volume_patches = {
    for name in keys(merge(var.control_plane_nodes, var.worker_nodes)) :
    name => contains(var.nodeid_encryption_nodes, name) ? local.system_volume_patches_nodeid : local.system_volume_patches_tpm
  }

  # Encrypted user volume "data" on the worker NVMe, for a local-path StorageClass.
  # The key scheme mirrors the system volumes so each node keeps one unlock mechanism
  # (TPM, or nodeID for var.nodeid_encryption_nodes).
  # minSize keeps a small or wrong NVMe from being claimed silently; no maxSize, so the
  # volume takes the whole disk.
  data_volume_patches_tpm = [
    yamlencode({
      apiVersion = "v1alpha1"
      kind       = "UserVolumeConfig"
      name       = "data"
      volumeType = "partition"
      provisioning = {
        diskSelector = {
          match = "disk.transport == \"nvme\""
        }
        minSize = "100GiB"
      }
      filesystem = {
        type = "xfs"
      }
      encryption = {
        provider = "luks2"
        keys     = [local.system_volume_tpm_key]
      }
    }),
  ]

  data_volume_patches_nodeid = [
    yamlencode({
      apiVersion = "v1alpha1"
      kind       = "UserVolumeConfig"
      name       = "data"
      volumeType = "partition"
      provisioning = {
        diskSelector = {
          match = "disk.transport == \"nvme\""
        }
        minSize = "100GiB"
      }
      filesystem = {
        type = "xfs"
      }
      encryption = {
        provider = "luks2"
        keys     = [{ slot = 0, nodeID = {} }]
      }
    }),
  ]

  data_volume_patches = {
    for name in keys(var.worker_nodes) :
    name => contains(var.nodeid_encryption_nodes, name) ? local.data_volume_patches_nodeid : local.data_volume_patches_tpm
  }

  # Documents that Talos accepts only on control plane machines
  # (container.ControlplaneOnlyConfig). Applying any of these to a worker is a hard
  # error: "the following document kinds are only allowed on control plane machines".
  control_plane_only_patches = [
    # Document: KubeProxyConfig - Disabled for Cilium (kube-proxy replacement)
    yamlencode({
      apiVersion = "v1alpha1"
      kind       = "KubeProxyConfig"
      enabled    = false
    }),
    # Document: KubeFlannelCNIConfig - Delete the default Flannel CNI for Cilium
    yamlencode({
      apiVersion = "v1alpha1"
      kind       = "KubeFlannelCNIConfig"
      "$patch"   = "delete"
    }),
  ]

  # Modern multi-document patches shared across all nodes (control plane + workers).
  # Split into head/tail so the PER-NODE system volume patches can be spliced in the
  # middle, keeping document order (and therefore the config hash) stable.
  common_patches_head = [
    # Document: UnattendedInstallConfig - install to the SATA SSD from the SecureBoot factory image
    yamlencode({
      apiVersion = "v1alpha1"
      kind       = "UnattendedInstallConfig"
      reboot     = true
      installer = {
        image = var.talos_installer_image
      }
      provisioning = {
        diskSelector = {
          match = "disk.dev_path == \"/dev/sda\""
        }
        wipe = true
      }
    }),
  ]

  common_patches_tail = [
    # Document: ResolverConfig - Upstream DNS
    yamlencode({
      apiVersion = "v1alpha1"
      kind       = "ResolverConfig"
      nameservers = [
        for ns in var.dns_nameservers : {
          address = ns
        }
      ]
    }),
    # Document: TimeSyncConfig - European NTP servers
    yamlencode({
      apiVersion = "v1alpha1"
      kind       = "TimeSyncConfig"
      ntp = {
        servers = var.ntp_servers
      }
    }),
    # Document: KubeNodeConfig - Node IP subnet
    yamlencode({
      apiVersion = "v1alpha1"
      kind       = "KubeNodeConfig"
      nodeIP = {
        validSubnets = [var.vlan_cidr]
      }
    }),
    # Document: KubeletConfig - Graceful shutdown
    yamlencode({
      apiVersion = "v1alpha1"
      kind       = "KubeletConfig"
      config = {
        shutdownGracePeriod             = "30s"
        shutdownGracePeriodCriticalPods = "10s"
      }
    }),
    # Document: KubeNetworkConfig - Pod and Service CIDRs
    yamlencode({
      apiVersion     = "v1alpha1"
      kind           = "KubeNetworkConfig"
      dnsDomain      = "cluster.local"
      podSubnets     = [var.pod_cidr]
      serviceSubnets = [var.service_cidr]
    }),
    # NOTE: control-plane-only documents (KubeProxyConfig, KubeFlannelCNIConfig,
    # KubeAPIServerConfig, ...) are NOT valid on worker machines - they live in
    # local.control_plane_only_patches.
  ]
}

resource "talos_machine_secrets" "this" {}

data "talos_machine_configuration" "control_plane" {
  for_each = var.control_plane_nodes

  cluster_name       = var.cluster_name
  machine_type       = "controlplane"
  cluster_endpoint   = "https://${var.cluster_vip}:6443"
  machine_secrets    = talos_machine_secrets.this.machine_secrets
  kubernetes_version = var.kubernetes_version
  talos_version      = var.talos_version

  config_patches = concat(
    [
      # Base v1alpha1 patch
      yamlencode({
        machine = local.common_v1alpha1_machine_patch
        cluster = {
          etcd = { advertisedSubnets = [var.vlan_cidr] }
        }
      }),
      # Node Hostname
      yamlencode({
        apiVersion = "v1alpha1"
        kind       = "HostnameConfig"
        auto       = "off"
        hostname   = each.value.hostname
      }),
      # Layer 2 Virtual IP for HA control plane
      yamlencode({
        apiVersion = "v1alpha1"
        kind       = "Layer2VIPConfig"
        name       = var.cluster_vip
        link       = var.cluster_vip_interface
      }),
      # KubeAPIServerConfig - certExtraSANs
      yamlencode({
        apiVersion = "v1alpha1"
        kind       = "KubeAPIServerConfig"
        certExtraSANs = distinct(concat(
          [var.cluster_vip, var.netbird_domain],
          local.all_node_ips
        ))
      })
    ],
    local.common_patches_head,
    local.system_volume_patches[each.key],
    local.common_patches_tail,
    local.control_plane_only_patches
  )
}

data "talos_machine_configuration" "worker" {
  for_each = var.worker_nodes

  cluster_name       = var.cluster_name
  machine_type       = "worker"
  cluster_endpoint   = "https://${var.cluster_vip}:6443"
  machine_secrets    = talos_machine_secrets.this.machine_secrets
  kubernetes_version = var.kubernetes_version
  talos_version      = var.talos_version

  config_patches = concat(
    [
      # Base v1alpha1 patch
      yamlencode({
        machine = local.common_v1alpha1_machine_patch
      }),
      # Node Hostname
      yamlencode({
        apiVersion = "v1alpha1"
        kind       = "HostnameConfig"
        auto       = "off"
        hostname   = each.value.hostname
      })
    ],
    local.common_patches_head,
    local.system_volume_patches[each.key],
    local.data_volume_patches[each.key],
    local.common_patches_tail
  )
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
  endpoint             = var.control_plane_nodes["cp-vdcj"].ip

  depends_on = [talos_machine_configuration_apply.control_plane]
}

resource "talos_cluster_kubeconfig" "this" {
  client_configuration = talos_machine_secrets.this.client_configuration
  node                 = var.control_plane_nodes["cp-vdcj"].ip
  endpoint             = var.control_plane_nodes["cp-vdcj"].ip

  depends_on = [talos_machine_bootstrap.this]
}

data "talos_client_configuration" "this" {
  cluster_name         = var.cluster_name
  client_configuration = talos_machine_secrets.this.client_configuration
  nodes                = local.all_node_ips
  endpoints            = [var.cluster_vip]
}
