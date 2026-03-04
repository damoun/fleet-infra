variable "sops_age_key" {
  type        = string
  sensitive   = true
  description = "age private key for SOPS decryption (AGE-SECRET-KEY-...)"
}
