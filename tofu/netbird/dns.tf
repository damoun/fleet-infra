data "netbird_group" "all" {
  name = "All"
}

locals {
  # Control plane node IPs on VLAN 40 — see tofu/baremetal/variables.tf
  control_plane_ips = ["192.168.40.11", "192.168.40.12", "192.168.40.13"]
}

resource "netbird_dns_zone" "damoun_internal" {
  name                 = "damoun.internal"
  domain               = "damoun.internal"
  enabled              = true
  enable_search_domain = true
  distribution_groups  = [data.netbird_group.all.id]
}

resource "netbird_dns_record" "kube_core_ams" {
  count   = length(local.control_plane_ips)
  zone_id = netbird_dns_zone.damoun_internal.id
  name    = "kube.core.ams.damoun.internal"
  type    = "A"
  content = local.control_plane_ips[count.index]
  ttl     = 300
}
