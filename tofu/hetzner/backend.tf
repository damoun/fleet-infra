# TODO: migrate to S3 backend once Hetzner Object Storage bucket is created
# Run: tofu init -migrate-state
#
# terraform {
#   backend "s3" {
#     bucket                      = "dapl-prd-htz-fsn-app-tofu-state"
#     key                         = "hetzner/terraform.tfstate"
#     region                      = "fsn1"
#     endpoints                   = { s3 = "https://fsn1.your-objectstorage.com" }
#     skip_credentials_validation = true
#     skip_metadata_api_check     = true
#     skip_region_validation      = true
#     skip_requesting_account_id  = true
#     use_path_style              = true
#   }
#
#   encryption {
#     key_provider "pbkdf2" "state" {
#       passphrase = var.state_passphrase
#     }
#
#     method "aes_gcm" "state" {
#       keys = key_provider.pbkdf2.state
#     }
#
#     state {
#       method   = method.aes_gcm.state
#       enforced = true
#     }
#
#     plan {
#       method   = method.aes_gcm.state
#       enforced = true
#     }
#   }
# }
