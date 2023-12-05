resource "cloudflare_ruleset" "waf_custom_rules" {
  for_each = toset([data.cloudflare_zone.dev.id, data.cloudflare_zone.cloud.id])
  zone_id = each.key
  name    = "Zone custom WAF ruleset"
  kind    = "zone"
  phase   = "http_request_firewall_custom"

  rules {
    enabled     = true
    description = "Firewall rule to block countries"
    expression  = "(ip.geoip.country in {\"CN\" \"IN\" \"KP\" \"RU\"})"
    action      = "block"
  }

  rules {
    enabled     = true
    description = "Firewall rule to block bots and threats determined by CF"
    expression  = "(cf.client.bot) or (cf.threat_score gt 14)"
    action      = "block"
  }
}
