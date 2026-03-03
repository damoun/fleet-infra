resource "hcloud_firewall" "cluster" {
  name = var.cluster_name

  # Kubernetes API
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "6443"
    source_ips = var.admin_cidrs
  }

  # Talos apid
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "50000"
    source_ips = var.admin_cidrs
  }

  # ICMP
  rule {
    direction  = "in"
    protocol   = "icmp"
    source_ips = ["0.0.0.0/0", "::/0"]
  }
}
