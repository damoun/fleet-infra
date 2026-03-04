output "sops_age_secret_name" {
  value = kubernetes_secret.sops_age.metadata[0].name
}

output "netbird_setup_key_secret_name" {
  value = kubernetes_secret.netbird_setup_key.metadata[0].name
}
