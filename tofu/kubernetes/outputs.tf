output "sops_age_secret_name" {
  value = kubernetes_secret.sops_age.metadata[0].name
}

