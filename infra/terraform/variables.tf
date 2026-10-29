variable "environment" {
  description = "Environment name"
  type        = string
  validation {
    condition     = can(values(["dev", "staging", "prod"]), var.environment)
    error_message = "environment must be one of: dev, staging, prod"
  }
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "southeastasia"
}

variable "vnet_cidr" {
  description = "VNet CIDR block"
  type        = string
  default     = "10.10.0.0/16"
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default = {
    managed-by = "terraform"
    pdpa-scope = "true"
  }
}
