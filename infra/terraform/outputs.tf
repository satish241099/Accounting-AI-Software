# Consolidated Landing Zone Outputs
#
# This is the machine-readable contract consumed by downstream tasks
# (KB-053 PostgreSQL/storage/servicebus/containerapps, KB-047 Kubernetes).
# Subnet names, NSG names, Key Vault URI and CMK IDs here are referenced
# verbatim in infra/README.md.

output "environment" {
  description = "Active environment (dev|staging|prod)"
  value       = var.environment
}

output "location" {
  description = "Azure region (southeastasia)"
  value       = var.location
}

# --- Network ---
output "vnet_id" {
  description = "ID of the environment VNet"
  value       = module.vnet.vnet_id
}

output "vnet_name" {
  description = "Name of the environment VNet"
  value       = module.vnet.vnet_name
}

output "resource_group_name" {
  description = "Name of the landing-zone resource group"
  value       = module.vnet.resource_group_name
}

output "subnet_ids" {
  description = "Map of subnet name to subnet ID (contract: see infra/README.md)"
  value       = module.vnet.subnet_ids
}

output "subnet_address_prefixes" {
  description = "Map of subnet name to CIDR (contract: see infra/README.md)"
  value       = module.vnet.subnet_address_prefixes
}

output "nsg_ids" {
  description = "Map of subnet name to NSG ID (contract: see infra/README.md)"
  value       = module.nsg.nsg_ids
}

output "firewall_id" {
  description = "ID of the Azure Firewall"
  value       = module.firewall.firewall_id
}

output "firewall_private_ip" {
  description = "Private IP of the Azure Firewall (UDR next-hop)"
  value       = module.firewall.firewall_private_ip
}

# --- Key Vault / CMK ---
output "key_vault_id" {
  description = "ID of the environment Key Vault"
  value       = module.keyvault.key_vault_id
}

output "key_vault_uri" {
  description = "URI of the environment Key Vault (contract: see infra/README.md)"
  value       = module.keyvault.key_vault_uri
}

output "key_vault_name" {
  description = "Name of the environment Key Vault"
  value       = module.keyvault.key_vault_name
}

output "cmk_key_id" {
  description = "Versioned ID of the per-env customer-managed key (CMK)"
  value       = module.keyvault.cmk_key_id
}

output "cmk_key_versionless_id" {
  description = "Versionless ID of the per-env CMK (rotation-safe reference)"
  value       = module.keyvault.cmk_key_versionless_id
}

output "key_vault_managed_identity_principal_id" {
  description = "Principal ID of the managed identity with Key Vault Crypto User role"
  value       = module.keyvault.managed_identity_principal_id
}

# --- Private Endpoints ---
output "private_endpoint_ids" {
  description = "Map of private endpoint name to resource ID (populated by KB-053)"
  value       = module.private_endpoints.private_endpoint_ids
}

# --- State Backend ---
output "tfstate_resource_group_name" {
  description = "Resource group hosting the Terraform state storage account"
  value       = module.state_backend.resource_group_name
}

output "tfstate_storage_account_name" {
  description = "Storage account hosting the Terraform state blobs"
  value       = module.state_backend.storage_account_name
}
