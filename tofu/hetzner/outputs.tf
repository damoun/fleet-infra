output "control_plane_ips" {
  value = module.hetzner.control_plane_ips
}

output "control_plane_internal_ips" {
  value = module.hetzner.control_plane_internal_ips
}

output "worker_ips" {
  value = module.hetzner.worker_ips
}
