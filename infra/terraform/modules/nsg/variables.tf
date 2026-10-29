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

variable "resource_group_name" {
  description = "Name of the resource group hosting the NSGs (from vnet module)"
  type        = string
}

variable "vnet_cidr" {
  description = "VNet CIDR block, used for intra-VNet allow rules"
  type        = string
}

variable "subnet_ids" {
  description = "Map of subnet names to subnet IDs for NSG association"
  type        = map(string)
}

variable "tags" {
  description = "Common tags applied to all resources"
  type        = map(string)
  default     = {}
}
