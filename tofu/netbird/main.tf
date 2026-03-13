data "terraform_remote_state" "hetzner" {
  backend = "local"
  config = {
    path = "../hetzner/terraform.tfstate"
  }
}

resource "netbird_dns_zone" "damoun_internal" {
  name                 = "damoun.internal"
  domain               = "damoun.internal"
  enabled              = true
  enable_search_domain = true
}

resource "netbird_dns_record" "kube_app_fsn" {
  zone_id = netbird_dns_zone.damoun_internal.id
  name    = "kube.app.fsn.damoun.internal"
  type    = "A"
  content = data.terraform_remote_state.hetzner.outputs.control_plane_internal_ips[0]
  ttl     = 300
}
