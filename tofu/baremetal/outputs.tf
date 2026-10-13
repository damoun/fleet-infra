output "kubeconfig" {
  value       = talos_cluster_kubeconfig.this.kubeconfig_raw
  description = "Raw Kubernetes admin kubeconfig"
  sensitive   = true
}

output "talosconfig" {
  value       = data.talos_client_configuration.this.talos_config
  description = "Talos client configuration"
  sensitive   = true
}

output "cluster_vip" {
  value       = var.cluster_vip
  description = "Virtual IP of the Kubernetes control plane"
}

output "control_plane_ips" {
  value       = local.control_plane_ips
  description = "List of control plane node IP addresses"
}

output "worker_ips" {
  value       = local.worker_ips
  description = "List of worker node IP addresses"
}
