variable "environment" {
  description = "Deployment environment (dev|staging|prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "southeastasia"
}

variable "prefix" {
  description = "Resource naming prefix"
  type        = string
  default     = "malaysia-saas"
}

variable "suffix" {
  description = "Short random suffix for globally-unique Key Vault name"
  type        = string
}

variable "allowed_subnet_ids" {
  description = "Subnet IDs permitted to reach the Key Vault over private network"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Common tags applied to all resources"
  type        = map(string)
  default     = {}
}
