resource "cloudflare_record" "gf" {
  zone_id = data.cloudflare_zone.cloud.zone_id
  name    = "gf"
  value   = cloudflare_tunnel.home.cname
  type    = "CNAME"
  proxied = true
}

resource "cloudflare_record" "grafana" {
  zone_id = data.cloudflare_zone.cloud.zone_id
  name    = "grafana"
  value   = cloudflare_tunnel.home.cname
  type    = "CNAME"
  proxied = true
}

resource "cloudflare_record" "code_server" {
  zone_id = data.cloudflare_zone.dev.zone_id
  name    = "code"
  value   = cloudflare_tunnel.home.cname
  type    = "CNAME"
  proxied = true
}
