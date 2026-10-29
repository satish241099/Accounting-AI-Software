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

variable "tags" {
  description = "Tags"
  type        = map(string)
  default     = {}
}