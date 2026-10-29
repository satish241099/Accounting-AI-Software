variable "environment" {
  description = "Deployment environment"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Must be dev, staging, or prod"
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
}

variable "prefix" {
  description = "Resource naming prefix"
  type        = string
  default     = "malaysia-saas"
}

variable "subnet_cidrs" {
  description = "Map of subnet names to CIDRs"
  type        = map(string)
}

variable "tags" {
  description = "Tags"
  type        = map(string)
  default     = {}
}