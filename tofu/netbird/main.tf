data "terraform_remote_state" "hetzner" {
  backend = "local"
  config = {
    path = "../hetzner/terraform.tfstate"
  }
}

resource "netbird_dns_zone" "tools_fsn_damoun_internal" {
  name                 = "tools.fsn.damoun.internal"
  domain               = "tools.fsn.damoun.internal"
  enabled              = true
  enable_search_domain = true
}

resource "netbird_dns_record" "kube_tools_fsn" {
  count   = length(data.terraform_remote_state.hetzner.outputs.control_plane_internal_ips)
  zone_id = netbird_dns_zone.tools_fsn_damoun_internal.id
  name    = "kube.tools.fsn.damoun.internal"
  type    = "A"
  content = data.terraform_remote_state.hetzner.outputs.control_plane_internal_ips[count.index]
  ttl     = 300
}
