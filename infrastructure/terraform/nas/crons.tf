resource "truenas_cronjob" "acme" {
  enabled     = true
  user        = "root"
  command     = "/root/.acme.sh/acme.sh --cron --home '/root/.acme.sh'"
  description = "Created by terraform"
  schedule {
    dom    = "*"
    dow    = "*"
    hour   = "3"
    minute = "48"
    month  = "*"
  }
  hide_stdout = true
}
