resource "azurerm_subnet_network_security_group_association" "assoc" {
  for_each                  = var.subnet_ids
  subnet_id                 = each.value
  network_security_group_id = azurerm_network_security_group.nsg[each.key].id
}

resource "azurerm_network_security_group" "nsg" {
  for_each            = var.subnet_ids
  name                = "nsg-${var.prefix}-${each.key}-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags

  security_rule {
    name                       = "allow-vnet-inbound"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = var.vnet_cidr
    destination_address_prefix = "*"
  }

  # Deny all other inbound traffic by default.
  security_rule {
    name                       = "deny-all-inbound"
    priority                   = 4096
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  # Allow outbound to VNet and Azure Cloud (service tags), deny internet egress by default.
  security_rule {
    name                       = "allow-vnet-outbound"
    priority                   = 100
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = var.vnet_cidr
  }

  security_rule {
    name                       = "allow-azure-cloud-outbound"
    priority                   = 200
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "AzureCloud"
  }

  # Deny all other outbound internet traffic by default.
  security_rule {
    name                       = "deny-all-outbound"
    priority                   = 4096
    direction                  = "Outbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}
