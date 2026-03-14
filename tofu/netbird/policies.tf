resource "netbird_policy" "admin_to_kubernetes" {
  name    = "Admin to Kubernetes"
  enabled = true

  rule {
    name          = "Allow TCP 6443"
    enabled       = true
    action        = "accept"
    protocol      = "tcp"
    ports         = ["6443"]
    sources       = [netbird_group.admins.id]
    destinations  = [netbird_group.kubernetes_admin.id]
    bidirectional = false
  }
}
