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

variable "resource_group_name" {
  description = "Name of the resource group hosting private endpoints and DNS zones"
  type        = string
}

variable "vnet_id" {
  description = "ID of the VNet to link private DNS zones to"
  type        = string
}

variable "subnet_id" {
  description = "ID of the subnet hosting the private endpoints (e.g. 'pe-private' subnet)"
  type        = string
}

variable "private_endpoints" {
  description = "Map of private endpoint name to its configuration"
  type = map(object({
    resource_id          = string
    subresource_names    = list(string)
    private_dns_zone_ids = list(string)
  }))
}

variable "private_dns_zones" {
  description = "Map of DNS zone key to its name (linked to the VNet)"
  type = map(object({
    zone_name = string
  }))
  default = {}
}

variable "tags" {
  description = "Common tags applied to all resources"
  type        = map(string)
  default     = {}
}
