output "nsg_ids" {
  description = "Map of subnet name to NSG ID"
  value       = { for k, v in azurerm_network_security_group.nsg : k => v.id }
}

output "nsg_names" {
  description = "Map of subnet name to NSG name"
  value       = { for k, v in azurerm_network_security_group.nsg : k => v.name }
}
