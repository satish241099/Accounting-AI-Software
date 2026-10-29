output "firewall_id" {
  description = "ID of the Azure Firewall"
  value       = azurerm_firewall.fw.id
}

output "firewall_name" {
  description = "Name of the Azure Firewall"
  value       = azurerm_firewall.fw.name
}

output "firewall_private_ip" {
  description = "Private IP of the Azure Firewall (next-hop for UDRs)"
  value       = azurerm_firewall.fw.ip_configuration[0].private_ip_address
}

output "firewall_public_ip" {
  description = "Public IP of the Azure Firewall"
  value       = azurerm_public_ip.firewall.ip_address
}

output "route_table_id" {
  description = "ID of the route table forcing egress through the firewall"
  value       = azurerm_route_table.fw_rt.id
}
