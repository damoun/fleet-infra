variable "cluster_name" {
  type    = string
  default = "dapl-prd-htz-fsn-app"
}

variable "kubernetes_version" {
  type    = string
  default = "1.35.0"
}

variable "network_cidr" {
  type    = string
  default = "172.16.16.0/20"
}

variable "node_subnet_cidr" {
  type    = string
  default = "172.16.16.0/24"
}

variable "pod_cidr" {
  type    = string
  default = "172.20.0.0/16"
}

variable "service_cidr" {
  type    = string
  default = "172.24.0.0/16"
}
