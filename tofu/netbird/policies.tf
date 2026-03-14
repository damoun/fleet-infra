resource "netbird_policy" "admin_to_kubernetes" {
  name        = "Admin to Kubernetes"
  description = "Managed by OpenTofu"
  enabled     = true

  rule {
    name          = "Allow TCP 6443"
    enabled       = true
    action        = "accept"
    protocol      = "tcp"
    ports         = ["6443"]
    sources       = [netbird_group.admin.id]
    destinations  = [netbird_group.kubernetes.id]
    bidirectional = false
  }
}
