output "private_endpoint_ids" {
  description = "Map of private endpoint name to its resource ID"
  value       = { for k, v in azurerm_private_endpoint.pe : k => v.id }
}

output "private_endpoint_ips" {
  description = "Map of private endpoint name to its assigned private IP"
  value       = { for k, v in azurerm_private_endpoint.pe : k => v.private_service_connection[0].private_ip_address }
}

output "private_dns_zone_ids" {
  description = "Map of DNS zone key to its resource ID"
  value = merge(
    { postgres = azurerm_private_dns_zone.postgres.id },
    { keyvault = azurerm_private_dns_zone.keyvault.id },
    { blob = azurerm_private_dns_zone.blob.id },
    { servicebus = azurerm_private_dns_zone.servicebus.id },
    { for k, v in azurerm_private_dns_zone_virtual_network_link.links : k => v.id }
  )
}
