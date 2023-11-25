resource "random_password" "tunnel_secret" {
  length = 64
}

resource "cloudflare_tunnel" "home" {
  account_id = data.cloudflare_accounts.account.accounts[0].id
  name       = "home"
  secret     = base64sha256(random_password.tunnel_secret.result)
}
