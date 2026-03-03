resource "hcloud_firewall" "cluster" {
  name = var.cluster_name

  # Kubernetes API
  dynamic "rule" {
    for_each = var.admin_cidrs
    content {
      direction  = "in"
      protocol   = "tcp"
      port       = "6443"
      source_ips = [rule.value]
    }
  }

  # Talos apid
  dynamic "rule" {
    for_each = var.admin_cidrs
    content {
      direction  = "in"
      protocol   = "tcp"
      port       = "50000"
      source_ips = [rule.value]
    }
  }

  # Talos trustd
  dynamic "rule" {
    for_each = var.admin_cidrs
    content {
      direction  = "in"
      protocol   = "tcp"
      port       = "50001"
      source_ips = [rule.value]
    }
  }

  # ICMP
  rule {
    direction  = "in"
    protocol   = "icmp"
    source_ips = ["0.0.0.0/0", "::/0"]
  }
}
