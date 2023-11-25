
module "home_automation" {
  source    = "./pv"
  namespace = "home-automation"
  pool      = var.truenas_pool
  volumes = [
    "home-assistant-storage",
  ]
  parent = truenas_dataset.kubernetes.name
}
