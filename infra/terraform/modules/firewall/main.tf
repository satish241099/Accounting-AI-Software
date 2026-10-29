resource "azurerm_public_ip" "firewall" {
  name                = "pip-fw-${var.prefix}-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = var.tags
}

resource "azurerm_firewall" "fw" {
  name                = "afw-${var.prefix}-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku_name            = "AZFW_VNet"
  sku_tier            = var.sku_tier
  firewall_policy_id  = azurerm_firewall_policy.fw_policy.id
  tags                = var.tags

  ip_configuration {
    name                 = "configuration"
    subnet_id            = var.firewall_subnet_id
    public_ip_address_id = azurerm_public_ip.firewall.id
  }
}

resource "azurerm_firewall_policy" "fw_policy" {
  name                     = "afwp-${var.prefix}-${var.environment}"
  location                 = var.location
  resource_group_name      = var.resource_group_name
  sku                      = var.sku_tier == "Standard" ? "Standard" : "Premium"
  threat_intelligence_mode = "Alert"
  tags                     = var.tags

  dns {
    proxy_enabled = true
  }
}

resource "azurerm_firewall_policy_rule_collection_group" "network" {
  name               = "rcg-${var.prefix}-${var.environment}"
  firewall_policy_id = azurerm_firewall_policy.fw_policy.id
  priority           = 200

  network_rule_collection {
    name     = "allow-azure-services-egress"
    priority = 100
    action   = "Allow"

    rule {
      name                  = "allow-to-azure-cloud"
      protocols             = ["Any"]
      source_addresses      = var.vnet_cidr != "" ? [var.vnet_cidr] : ["*"]
      destination_addresses = ["AzureCloud"]
      destination_ports     = ["*"]
    }
  }

  application_rule_collection {
    name     = "allow-os-updates"
    priority = 200
    action   = "Allow"

    rule {
      name              = "allow-windows-update"
      source_addresses  = var.vnet_cidr != "" ? [var.vnet_cidr] : ["*"]
      destination_fqdns = ["*.windowsupdate.com", "*.update.microsoft.com"]
      protocols {
        port = "443"
        type = "Https"
      }
    }
  }
}

resource "azurerm_route_table" "fw_rt" {
  name                = "rt-${var.prefix}-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags

  route {
    name                   = "default-via-firewall"
    address_prefix         = "0.0.0.0/0"
    next_hop_type          = "VirtualAppliance"
    next_hop_in_ip_address = azurerm_firewall.fw.ip_configuration[0].private_ip_address
  }
}

resource "azurerm_subnet_route_table_association" "workload_subnets" {
  for_each       = var.subnet_ids
  subnet_id      = each.value
  route_table_id = azurerm_route_table.fw_rt.id
}
