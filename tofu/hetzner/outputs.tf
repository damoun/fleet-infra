output "kubeconfig" {
  value     = talos_cluster_kubeconfig.this.kubeconfig_raw
  sensitive = true
}

output "talosconfig" {
  value     = data.talos_client_configuration.this.talos_config
  sensitive = true
}

output "load_balancer_ip" {
  value = hcloud_load_balancer.api.ipv4
}

output "control_plane_ips" {
  value = [for s in hcloud_server.control_plane : s.ipv4_address]
}

output "worker_ips" {
  value = [for s in hcloud_server.worker : s.ipv4_address]
}
