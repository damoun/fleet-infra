resource "cloudflare_record" "gf" {
  zone_id = data.cloudflare_zone.zone.zone_id
  name    = "gf"
  value   = cloudflare_tunnel.home.cname
  type    = "CNAME"
  proxied = true
}

resource "cloudflare_record" "grafana" {
  zone_id = data.cloudflare_zone.zone.zone_id
  name    = "grafana"
  value   = cloudflare_tunnel.home.cname
  type    = "CNAME"
  proxied = true
}

resource "cloudflare_tunnel_config" "grafana" {
  account_id = data.cloudflare_accounts.account.accounts[0].id
  tunnel_id  = cloudflare_tunnel.home.id

  config {
    ingress_rule {
      hostname = cloudflare_record.grafana.hostname
      service  = "http://grafana.monitoring.svc.cluster.local."
    }
    ingress_rule {
      hostname = cloudflare_record.gf.hostname
      service  = "http://grafana.monitoring.svc.cluster.local."
    }
    ingress_rule {
      service = "http_status:404"
    }
  }
}
