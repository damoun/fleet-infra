variable "netbird_api_token" {
  type      = string
  sensitive = true
}

variable "cluster_name" {
  type    = string
  default = "dapl-prd-htz-fsn-app"
}
