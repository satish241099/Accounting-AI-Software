variable "environment" {
  description = "Deployment environment (dev|staging|prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "location" {
  description = "Azure region (PDPA: all customer data stays in southeastasia)"
  type        = string
  default     = "southeastasia"
}

variable "vnet_cidr" {
  description = "VNet CIDR override; when empty, per-environment defaults from main.tf locals are used"
  type        = string
  default     = ""
}

variable "private_endpoints" {
  description = "Map of private endpoint name to configuration (populated by KB-053 when resources exist)"
  type = map(object({
    resource_id          = string
    subresource_names    = list(string)
    private_dns_zone_ids = list(string)
  }))
  default = {}
}

variable "tags" {
  description = "Common tags applied to all resources"
  type        = map(string)
  default = {
    managed-by = "terraform"
    pdpa-scope = "true"
    project    = "malaysia-accounting-saas"
  }
}
