output "sops_age_secret_name" {
  value = kubernetes_secret_v1.sops_age.metadata[0].name
}

