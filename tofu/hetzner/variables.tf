variable "hcloud_token" {
  type      = string
  sensitive = true
}

variable "cluster_name" {
  type    = string
  default = "dapl-prd-htz-fsn-app"
}

variable "location" {
  type    = string
  default = "fsn1"
}

variable "talos_version" {
  type    = string
  default = "v1.12.4"
}

variable "server_type" {
  type    = string
  default = "cx23"
}

variable "control_plane_count" {
  type    = number
  default = 3
}

variable "worker_count" {
  type    = number
  default = 3
}

variable "admin_cidrs" {
  type        = list(string)
  description = "CIDRs allowed to reach K8s API and Talos endpoints"
}

variable "network_cidr" {
  type    = string
  default = "172.16.16.0/20"
}

variable "node_subnet_cidr" {
  type    = string
  default = "172.16.16.0/24"
}

