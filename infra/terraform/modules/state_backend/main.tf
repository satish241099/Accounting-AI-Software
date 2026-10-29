resource "azurerm_resource_group" "tfstate" {
  name     = "rg-tfstate-${var.environment}-${replace(var.location, " ", "")}"
  location = var.location
  tags     = var.tags
}

resource "azurerm_storage_account" "tfstate" {
  name                          = "${var.environment}tfstate${substr(md5(random_id.salt.hex), 0, 6)}"
  resource_group_name           = azurerm_resource_group.tfstate.name
  location                      = var.location
  account_tier                  = "Standard"
  account_replication_type      = "LRS"
  min_tls_version               = "TLS1_2"
  public_network_access_enabled = false
  is_hns_enabled                = true

  tags = var.tags
}

resource "azurerm_storage_container" "tfstate" {
  name                  = "tfstate"
  storage_account_id    = azurerm_storage_account.tfstate.id
  container_access_type = "private"
}

resource "random_id" "salt" {
  byte_length = 4
}