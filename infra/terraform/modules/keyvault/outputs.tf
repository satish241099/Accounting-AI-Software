output "key_vault_id" {
  description = "ID of the Key Vault"
  value       = azurerm_key_vault.kv.id
}

output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = azurerm_key_vault.kv.name
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.kv.vault_uri
}

output "cmk_key_id" {
  description = "ID of the customer-managed key (CMK) for per-env encryption"
  value       = azurerm_key_vault_key.cmk.id
}

output "cmk_key_versionless_id" {
  description = "Versionless ID of the CMK (for rotation-safe references)"
  value       = azurerm_key_vault_key.cmk.versionless_id
}

output "managed_identity_id" {
  description = "ID of the user-assigned managed identity with Key Vault Crypto User role"
  value       = azurerm_user_assigned_identity.keyvault.id
}

output "managed_identity_principal_id" {
  description = "Principal ID of the user-assigned managed identity"
  value       = azurerm_user_assigned_identity.keyvault.principal_id
}

output "resource_group_name" {
  description = "Name of the resource group hosting the Key Vault"
  value       = azurerm_resource_group.keyvault.name
}

output "secret_names" {
  description = "Secret naming convention per infra/README.md contract"
  value = {
    db_admin = azurerm_key_vault_secret.db_admin.name
    db_app   = azurerm_key_vault_secret.db_app.name
  }
}
