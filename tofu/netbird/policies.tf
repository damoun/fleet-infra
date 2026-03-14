resource "netbird_policy" "kubernetes_admin" {
  name    = "kubernetes.admin"
  enabled = true

  rule {
    name          = "Allow TCP 6443"
    enabled       = true
    action        = "accept"
    protocol      = "tcp"
    ports         = ["6443"]
    sources       = [netbird_group.admin.id]
    destinations  = [netbird_group.kubernetes_admin.id]
    bidirectional = false
  }
}
