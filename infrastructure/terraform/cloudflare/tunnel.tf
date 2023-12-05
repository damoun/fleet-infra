resource "random_password" "tunnel_secret" {
  length = 64
}

resource "cloudflare_tunnel" "home" {
  account_id = data.cloudflare_accounts.account.accounts[0].id
  name       = "home"
  secret     = base64sha256(random_password.tunnel_secret.result)
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
      hostname = cloudflare_record.code_server.hostname
      service  = "http://code-server.develop.svc.cluster.local."
    }
    ingress_rule {
      service = "http_status:404"
    }
  }
}
