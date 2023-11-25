variable "truenas_api_key" {
  description = "API key for the TrueNAS server"
  sensitive   = true
}

variable "truenas_base_url" {
  type        = string
  description = "Base url for the TrueNAS server"
  sensitive   = true
}

variable "truenas_debug" {
  type        = string
  description = "Enable debug from the TrueNAS provider"
  default     = false
}

variable "truenas_pool" {
  type        = string
  description = "Name of the pool to use on the TrueNAS server"
  default     = "pool1"
}
