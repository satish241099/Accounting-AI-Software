resource "azurerm_resource_group" "network" {
  name     = "rg-${var.prefix}-net-${var.environment}"
  location = var.location
  tags     = var.tags
}

resource "azurerm_virtual_network" "main" {
  name                = "vnet-${var.prefix}-${var.environment}"
  address_space       = [var.vnet_cidr]
  location            = var.location
  resource_group_name = azurerm_resource_group.network.name
  tags                = var.tags
}

resource "azurerm_subnet" "subnets" {
  for_each             = var.subnet_cidrs
  name                 = each.key
  resource_group_name  = azurerm_resource_group.network.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = [each.value]

  private_endpoint_network_policies             = "Enabled"
  private_link_service_network_policies_enabled = true
}