output "vnet_id" {
  description = "ID of the main VNet"
  value       = azurerm_virtual_network.main.id
}

output "vnet_name" {
  description = "Name of the main VNet"
  value       = azurerm_virtual_network.main.name
}

output "resource_group_name" {
  description = "Name of the resource group hosting the VNet"
  value       = azurerm_resource_group.network.name
}

output "resource_group_id" {
  description = "ID of the resource group hosting the VNet"
  value       = azurerm_resource_group.network.id
}

output "subnet_ids" {
  description = "Map of subnet name to subnet ID"
  value       = { for k, v in azurerm_subnet.subnets : k => v.id }
}

output "subnet_address_prefixes" {
  description = "Map of subnet name to its CIDR prefix"
  value       = { for k, v in azurerm_subnet.subnets : k => v.address_prefixes[0] }
}
