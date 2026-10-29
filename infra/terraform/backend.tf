terraform {
  backend "azurerm" {
    resource_group_name   = var.state_rg_name
    storage_account_name  = var.state_storage_account
    container_name        = "tfstate"
    key                   = "landingzone.${var.environment}.tfstate"
    use_azuread_auth      = true
  }
}
