resource "azurerm_private_dns_zone" "postgres" {
  name                = "privatelink.postgres.database.azure.com"
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_private_dns_zone" "keyvault" {
  name                = "privatelink.vaultcore.azure.net"
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_private_dns_zone" "blob" {
  name                = "privatelink.blob.core.windows.net"
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_private_dns_zone" "servicebus" {
  name                = "privatelink.servicebus.windows.net"
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "links" {
  for_each             = var.private_dns_zones
  name                 = "link-${each.key}-${var.environment}"
  resource_group_name  = var.resource_group_name
  private_dns_zone_id  = azurerm_private_dns_zone[each.key].id
  virtual_network_id   = var.vnet_id
  registration_enabled = false
  tags                 = var.tags
}

resource "azurerm_private_endpoint" "pe" {
  for_each            = var.private_endpoints
  name                = "pe-${each.key}-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.subnet_id
  tags                = var.tags

  private_service_connection {
    name                           = "psc-${each.key}-${var.environment}"
    private_connection_resource_id = each.value.resource_id
    subresource_names              = each.value.subresource_names
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "pdzg-${each.key}"
    private_dns_zone_ids = each.value.private_dns_zone_ids
  }
}