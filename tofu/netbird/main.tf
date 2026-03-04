resource "netbird_setup_key" "cluster" {
  name           = var.cluster_name
  type           = "reusable"
  expiry_seconds = 0
  usage_limit    = 0
}
