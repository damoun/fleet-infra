data "netbird_group" "all" {
  name = "All"
}

locals {
  # Control plane Layer-2 virtual IP — the Kubernetes API endpoint, matching
  # var.cluster_vip in tofu/baremetal. The VIP moves between control plane nodes
  # on its own, so a single stable record is preferred over one per node.
  cluster_vip = "192.168.40.10"
}

resource "netbird_dns_zone" "damoun_internal" {
  name                 = "damoun.internal"
  domain               = "damoun.internal"
  enabled              = true
  enable_search_domain = true
  distribution_groups  = [data.netbird_group.all.id]
}

resource "netbird_dns_record" "kube_core_ams" {
  zone_id = netbird_dns_zone.damoun_internal.id
  name    = "kube.core.ams.damoun.internal"
  type    = "A"
  content = local.cluster_vip
  ttl     = 300
}
