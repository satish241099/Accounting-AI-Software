resource "azurerm_resource_group" "keyvault" {
  name     = "rg-${var.prefix}-kv-${var.environment}"
  location = var.location
  tags     = var.tags
}

resource "azurerm_user_assigned_identity" "keyvault" {
  name                = "id-${var.prefix}-kv-${var.environment}"
  location            = var.location
  resource_group_name = azurerm_resource_group.keyvault.name
  tags                = var.tags
}

resource "azurerm_key_vault" "kv" {
  name                       = "kv-${var.prefix}-${var.environment}-${var.suffix}"
  location                   = var.location
  resource_group_name        = azurerm_resource_group.keyvault.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "premium"
  rbac_authorization_enabled = true
  purge_protection_enabled   = true
  soft_delete_retention_days = 90
  public_network_access_enabled = false
  tags                       = var.tags

  network_acls {
    bypass                     = "AzureServices"
    default_action             = "Deny"
    virtual_network_subnet_ids = var.allowed_subnet_ids
  }
}

data "azurerm_client_config" "current" {}

# Customer-managed key (CMK) for encrypting secrets and backing disks.
resource "azurerm_key_vault_key" "cmk" {
  name         = "cmk-${var.prefix}-${var.environment}"
  key_vault_id = azurerm_key_vault.kv.id
  key_type     = "RSA-HSM"
  key_size     = 3072
  key_opts     = ["unwrapKey", "wrapKey"]

  rotation_policy {
    expire_after         = "P90D"
    notify_before_expiry = "P30D"

    automatic {
      time_before_expiry = "P30D"
    }
  }

  expiration_date = "2027-12-31T23:59:59Z" # 1 year from 2026-10-29

  depends_on = [azurerm_role_assignment.kv_crypto_officer]
}

resource "azurerm_role_assignment" "kv_crypto_officer" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Crypto Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Grant the managed identity access to wrap/unwrap the CMK (for downstream consumers like PostgreSQL/Storage encryption).
resource "azurerm_role_assignment" "keyvault_identity_crypto_user" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Crypto User"
  principal_id         = azurerm_user_assigned_identity.keyvault.principal_id
}

# Placeholder secret references. Actual secret VALUES are injected by downstream tasks (KB-053),
# not hardcoded here. We reserve the naming convention per infra/README.md contract.

resource "azurerm_key_vault_secret" "db_admin" {
  name            = "db/${var.environment}/admin"
  value           = "placeholder-change-me"
  key_vault_id    = azurerm_key_vault.kv.id
  content_type    = "text/plain"
  expiration_date = "2027-01-27T23:59:59Z" # 90 days from 2026-10-29

  depends_on = [azurerm_role_assignment.kv_secrets_officer]
}

resource "azurerm_key_vault_secret" "db_app" {
  name            = "db/${var.environment}/postgres"
  value           = "placeholder-change-me"
  key_vault_id    = azurerm_key_vault.kv.id
  content_type    = "text/plain"
  expiration_date = "2027-01-27T23:59:59Z" # 90 days from 2026-10-29

  depends_on = [azurerm_role_assignment.kv_secrets_officer]
}

resource "azurerm_role_assignment" "kv_secrets_officer" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}
