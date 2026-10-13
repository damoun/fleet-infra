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
    "cp-node2" = {
      ip       = "192.168.40.12"
      hostname = "cp-node2"
    }
    "cp-node3" = {
      ip       = "192.168.40.13"
      hostname = "cp-node3"
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
    "w-node1" = {
      ip       = "192.168.40.21"
      hostname = "w-node1"
    }
    "w-node2" = {
      ip       = "192.168.40.22"
      hostname = "w-node2"
    }
    "w-node3" = {
      ip       = "192.168.40.23"
      hostname = "w-node3"
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
  default     = "1.35.0"
}

variable "talos_version" {
  type        = string
  description = "Talos Linux machine configuration version"
  default     = "v1.12.4"
}
