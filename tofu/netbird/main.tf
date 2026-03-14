data "netbird_group" "admins" {
  name = "admins"
}

locals {
  control_plane_ips = ["172.16.16.5", "172.16.16.6", "172.16.16.7"]
}

resource "netbird_dns_zone" "tools_fsn_damoun_internal" {
  name                 = "tools.fsn.damoun.internal"
  domain               = "tools.fsn.damoun.internal"
  enabled              = true
  enable_search_domain = true
  distribution_groups  = [data.netbird_group.admins.id]
}

resource "netbird_dns_record" "kube_tools_fsn" {
  count   = length(local.control_plane_ips)
  zone_id = netbird_dns_zone.tools_fsn_damoun_internal.id
  name    = "kube.tools.fsn.damoun.internal"
  type    = "A"
  content = local.control_plane_ips[count.index]
  ttl     = 300
}
