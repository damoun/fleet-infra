variable "cluster_name" {
  type        = string
  description = "Name of the Kubernetes cluster"
  default     = "dapl-prd-hom-ams-core"
}

variable "cluster_vip" {
  type        = string
  description = "Virtual IP for the HA Kubernetes control plane"
  default     = "192.168.40.10"
}

variable "cluster_vip_interface" {
  type        = string
  description = "Network interface name where the VIP is bound (eno1 on HP EliteDesk 800 G2 onboard NIC)"
  default     = "eno1"
}

variable "control_plane_nodes" {
  type = map(object({
    ip       = string
    hostname = string
  }))
  description = "Map of control plane nodes with their static Omada DHCP IPs and hostnames (cp-<4char> pattern)"
  default = {
    "cp-vdcj" = {
      ip       = "192.168.40.11"
      hostname = "cp-vdcj"
    }
    "cp-eqwd" = {
      ip       = "192.168.40.12"
      hostname = "cp-eqwd"
    }
    "cp-hiuw" = {
      ip       = "192.168.40.13"
      hostname = "cp-hiuw"
    }
  }
}

variable "worker_nodes" {
  type = map(object({
    ip       = string
    hostname = string
  }))
  description = "Map of worker nodes with their static Omada DHCP IPs and hostnames (w-<4char> pattern)"
  default = {
    "w-ofph" = {
      ip       = "192.168.40.21"
      hostname = "w-ofph"
    }
    "w-jsai" = {
      ip       = "192.168.40.22"
      hostname = "w-jsai"
    }
    "w-jzax" = {
      ip       = "192.168.40.23"
      hostname = "w-jzax"
    }
  }
}

variable "gateway" {
  type        = string
  description = "Default gateway for VLAN 40"
  default     = "192.168.40.1"
}

variable "vlan_cidr" {
  type        = string
  description = "VLAN 40 subnet CIDR"
  default     = "192.168.40.0/24"
}

variable "dns_nameservers" {
  type        = list(string)
  description = "Upstream DNS resolvers"
  default     = ["192.168.40.1", "9.9.9.9"]
}

variable "ntp_servers" {
  type        = list(string)
  description = "European NTP servers for accurate time synchronization"
  default     = ["0.nl.pool.ntp.org", "1.nl.pool.ntp.org", "2.europe.pool.ntp.org"]
}

variable "netbird_domain" {
  type        = string
  description = "FQDN for control plane access over NetBird overlay mesh"
  default     = "kube.core.ams.damoun.internal"
}

variable "pod_cidr" {
  type        = string
  description = "Pod network CIDR (/20 supports up to 32 nodes with /25 per-node allocation)"
  default     = "172.20.0.0/20"
}

variable "service_cidr" {
  type        = string
  description = "Kubernetes Service network CIDR"
  default     = "172.24.0.0/16"
}

variable "kubernetes_version" {
  type        = string
  description = "Kubernetes version to bootstrap"
  # renovate: datasource=github-releases depName=kubernetes/kubernetes
  default = "1.35.9"
}

variable "talos_version" {
  type        = string
  description = "Talos Linux machine configuration version"
  default     = "v1.14.2"
}

variable "talos_installer_image" {
  type        = string
  description = "Talos Image Factory SecureBoot installer (i915, ucode, storage extensions; enrollKeys: force)"
  # renovate: datasource=github-releases depName=siderolabs/talos
  default = "factory.talos.dev/metal-installer-secureboot/7c67ed0c9d9cd774e2164b84cd41733c8b3432f83e44a7dc3cc23062bc4f89e2:v1.14.5"
}

variable "nodeid_encryption_nodes" {
  type        = list(string)
  description = <<-EOT
    Node keys (as used in control_plane_nodes / worker_nodes) that must encrypt their
    system volumes with the nodeID provider instead of TPM 2.0.

    Use this for HP EliteDesk 800 G2 units whose Infineon TPM is stuck in 1.2 mode:
    Talos only supports TPM 2.0, and HP's 1.2->2.0 conversion tool is Windows-only.
    nodeID derives the LUKS key from the motherboard UUID and needs no TPM.

    This can be reversed later without reinstalling - Talos reconciles encryption keys
    and adds a missing key slot to the existing LUKS container.
  EOT
  # Units confirmed to have a TPM 1.2-only Infineon chip:
  #   w-ofph  - tpm_version_major=1, no /dev/tpmrm0
  #   w-jsai  - dmesg "tpm_tis 00:06: 1.2 TPM", "TPM device is not a TPM 2.0"
  # CP nodes cp-vdcj/cp-eqwd/cp-hiuw report tpm_version_major=2 and keep the TPM path.
  # Add further worker names here as they are checked (talosctl read /sys/class/tpm/tpm0/tpm_version_major).
  default = ["w-ofph", "w-jsai"]
}
