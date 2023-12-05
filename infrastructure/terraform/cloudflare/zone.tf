data "cloudflare_zone" "cloud" {
  name = "damoun.cloud"
}

data "cloudflare_zone" "dev" {
  name = "damoun.dev"
}

data "cloudflare_zone" "games" {
  name = "damoun.games"
}
