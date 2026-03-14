data "netbird_group" "all" {
  name = "All"
}

locals {
  control_plane_ips = ["172.16.16.5", "172.16.16.6", "172.16.16.7"]
}

resource "netbird_dns_zone" "damoun_internal" {
  name                 = "damoun.internal"
  domain               = "damoun.internal"
  enabled              = true
  enable_search_domain = true
  distribution_groups  = [data.netbird_group.all.id]
}

resource "netbird_dns_record" "kube_tools_fsn" {
  count   = length(local.control_plane_ips)
  zone_id = netbird_dns_zone.damoun_internal.id
  name    = "kube.tools.fsn.damoun.internal"
  type    = "A"
  content = local.control_plane_ips[count.index]
  ttl     = 300
}
