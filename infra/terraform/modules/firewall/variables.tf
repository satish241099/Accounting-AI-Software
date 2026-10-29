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
  description = "Name of the resource group hosting the firewall"
  type        = string
}

variable "firewall_subnet_id" {
  description = "ID of the AzureFirewallSubnet dedicated subnet"
  type        = string
}

variable "vnet_cidr" {
  description = "VNet CIDR block, used as the source for allow rules"
  type        = string
  default     = ""
}

variable "sku_tier" {
  description = "Azure Firewall SKU tier (Standard|Premium)"
  type        = string
  default     = "Standard"
  validation {
    condition     = contains(["Standard", "Premium"], var.sku_tier)
    error_message = "SKU tier must be Standard or Premium."
  }
}

variable "subnet_ids" {
  description = "Map of subnet name to subnet ID for UDR association (workload subnets route egress through the firewall)"
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "Common tags applied to all resources"
  type        = map(string)
  default     = {}
}
