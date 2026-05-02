module "hetzner" {
  source = "git::https://github.com/damoun/terraform-hcloud-talos.git?ref=v1.0.0"

  cluster_name         = var.cluster_name
  location             = var.location
  talos_version        = var.talos_version
  server_type          = var.server_type
  control_plane_count  = var.control_plane_count
  worker_count         = var.worker_count
  admin_cidrs          = var.admin_cidrs
  network_cidr         = var.network_cidr
  node_subnet_cidr     = var.node_subnet_cidr
  enable_load_balancer = true
}
