# Root Terraform Composition — Malaysia Accounting SaaS Landing Zone
#
# Composes the reusable modules under modules/ into a single environment-scoped
# landing zone deployment. Select the environment via -var or terraform.tfvars.
# Per-environment state isolation is provided by the backend key in backend.tf
# (landingzone.{environment}.tfstate) and unique storage accounts per environment.

locals {
  environment = var.environment
  is_prod     = var.environment == "prod"

  # Per-environment defaults (PDPA: everything stays in southeastasia).
  vnet_cidrs = {
    dev     = "10.10.0.0/16"
    staging = "10.20.0.0/16"
    prod    = "10.30.0.0/16"
  }

  subnet_cidrs = {
    dev = {
      "snet-app"            = "10.10.1.0/24"
      "snet-db-private"     = "10.10.2.0/24"
      "snet-pe-private"     = "10.10.3.0/24"
      "AzureFirewallSubnet" = "10.10.254.0/26"
    }
    staging = {
      "snet-app"            = "10.20.1.0/24"
      "snet-db-private"     = "10.20.2.0/24"
      "snet-pe-private"     = "10.20.3.0/24"
      "AzureFirewallSubnet" = "10.20.254.0/26"
    }
    prod = {
      "snet-app"            = "10.30.1.0/24"
      "snet-db-private"     = "10.30.2.0/24"
      "snet-pe-private"     = "10.30.3.0/24"
      "AzureFirewallSubnet" = "10.30.254.0/26"
    }
  }

  vnet_cidr    = var.vnet_cidr != "" ? var.vnet_cidr : local.vnet_cidrs[var.environment]
  subnets_cidr = local.subnet_cidrs[var.environment]
}

# ---------------------------------------------------------------------------
# State backend (bootstrap; normally applied once per environment, then
# referenced via backend.tf for all subsequent runs)
# ---------------------------------------------------------------------------
module "state_backend" {
  source = "./modules/state_backend"

  environment = local.environment
  location    = var.location
  tags        = var.tags
}

# ---------------------------------------------------------------------------
# Network foundation: VNet, subnets (app / db-private / pe-private / firewall)
# ---------------------------------------------------------------------------
module "vnet" {
  source = "./modules/vnet"

  environment  = local.environment
  location     = var.location
  vnet_cidr    = local.vnet_cidr
  subnet_cidrs = local.subnets_cidr
  tags         = var.tags
}

# ---------------------------------------------------------------------------
# NSGs: deny-by-default with intra-VNet allow and Azure service-tag egress
# ---------------------------------------------------------------------------
module "nsg" {
  source = "./modules/nsg"

  environment         = local.environment
  location            = var.location
  resource_group_name = module.vnet.resource_group_name
  vnet_cidr           = local.vnet_cidr
  subnet_ids          = module.vnet.subnet_ids
  tags                = var.tags
}

# ---------------------------------------------------------------------------
# Azure Firewall: forced-tunnel egress with DNS proxy and threat intel (Alert)
# ---------------------------------------------------------------------------
module "firewall" {
  source = "./modules/firewall"

  environment         = local.environment
  location            = var.location
  resource_group_name = module.vnet.resource_group_name
  vnet_cidr           = local.vnet_cidr
  firewall_subnet_id  = module.vnet.subnet_ids["AzureFirewallSubnet"]
  subnet_ids = {
    "snet-app"        = module.vnet.subnet_ids["snet-app"]
    "snet-db-private" = module.vnet.subnet_ids["snet-db-private"]
  }
  tags = var.tags
}

# ---------------------------------------------------------------------------
# Key Vault with per-environment CMK (RSA-HSM 3072, 90-day rotation)
# ---------------------------------------------------------------------------
module "keyvault" {
  source = "./modules/keyvault"

  environment = local.environment
  location    = var.location
  suffix      = random_id.kv_suffix.hex
  allowed_subnet_ids = [
    module.vnet.subnet_ids["snet-app"],
    module.vnet.subnet_ids["snet-pe-private"],
  ]
  tags = var.tags
}

resource "random_id" "kv_suffix" {
  byte_length = 2
}

# ---------------------------------------------------------------------------
# Private endpoints for downstream services (KB-053 wires actual resource IDs)
# ---------------------------------------------------------------------------
module "private_endpoints" {
  source = "./modules/private_endpoints"

  environment         = local.environment
  location            = var.location
  resource_group_name = module.vnet.resource_group_name
  vnet_id             = module.vnet.vnet_id
  subnet_id           = module.vnet.subnet_ids["snet-pe-private"]
  private_dns_zones = {
    postgres = { zone_name = "privatelink.postgres.database.azure.com" }
  }
  private_endpoints = var.private_endpoints
  tags              = var.tags
}
