# Malaysia Accounting SaaS — Azure Landing Zone Infrastructure Contract

**Version:** 1.0 · **Date:** 2026-10-29 · **Owner:** Cloud Engineer (agent-1ec17107)  
**Mission:** M-MVKTMUFU-000V-OQTS (Malaysia Accounting SaaS Core Foundation)  
**Feature:** F-MVKTMUZ1-001P-ZHB3 (Azure Infrastructure)  
**PDPA Compliance:** All resources deployed in `southeastasia` (Azure Malaysia region)

---

## Overview

This document is the **machine-readable contract** for downstream infrastructure and application teams. It enumerates the subnet IDs, NSG IDs, Key Vault URIs, secret names, CMK references, and Terraform state backend coordinates produced by the landing zone Terraform modules (`infra/terraform/modules/`).

**Consumers:**
- **KB-053** — Provision Azure Malaysia Accounting SaaS Core Infrastructure (PostgreSQL, Storage, Service Bus, Container Apps)
- **KB-047** — Kubernetes manifests and cluster configuration
- **Database Engineer (agent-dcc4da7f)** — PostgreSQL connection configuration and secret wiring
- **Kubernetes Engineer (agent-d609c639)** — Secret mounting, network policy, and probe configuration

**Data Residency:** All resources are deployed in `southeastasia` (Azure Malaysia). No client financial data leaves this region (PDPA 2024 compliance).

---

## Environment Configuration

| Environment | VNet CIDR | App Subnet | DB Subnet | PE Subnet | Firewall Subnet |
|-------------|-----------|------------|-----------|-----------|-----------------|
| **dev** | `10.10.0.0/16` | `10.10.1.0/24` | `10.10.2.0/24` | `10.10.3.0/24` | `10.10.254.0/26` |
| **staging** | `10.20.0.0/16` | `10.20.1.0/24` | `10.20.2.0/24` | `10.20.3.0/24` | `10.20.254.0/26` |
| **prod** | `10.30.0.0/16` | `10.30.1.0/24` | `10.30.2.0/24` | `10.30.3.0/24` | `10.30.254.0/26` |

**Selection:** Set `var.environment` to `dev`, `staging`, or `prod` when running Terraform.

---

## Terraform State Backend

Remote state is stored per-environment in an Azure Storage Account.

| Output Key | Description | Example Value |
|------------|-------------|---------------|
| `tfstate_resource_group_name` | Resource group hosting state storage | `rg-tfstate-dev-southeastasia` |
| `tfstate_storage_account_name` | Storage account name | `sttfstatedevsea` |
| `tfstate_container_name` | Container name (fixed) | `tfstate` |
| Backend key | State blob path | `landingzone.{environment}.tfstate` |

**Usage:**
```hcl
terraform {
  backend "azurerm" {
    resource_group_name   = var.state_rg_name
    storage_account_name  = var.state_storage_account
    container_name        = "tfstate"
    key                   = "landingzone.${var.environment}.tfstate"
    use_azuread_auth      = true
  }
}
```

---

## Network Foundation

### VNet and Subnets

| Output Key | Description | Type |
|------------|-------------|------|
| `vnet_id` | VNet resource ID | `string` |
| `vnet_name` | VNet name | `string` |
| `resource_group_name` | Network resource group | `string` |
| `subnet_ids` | Map: subnet name → subnet ID | `map(string)` |
| `subnet_address_prefixes` | Map: subnet name → CIDR | `map(string)` |

**Subnet Names (contract):**
- `snet-app` — Application tier (Container Apps, app services)
- `snet-db-private` — Database tier (PostgreSQL private endpoint)
- `snet-pe-private` — Private endpoints for all PaaS services
- `AzureFirewallSubnet` — Azure Firewall (forced egress)

**Usage (KB-053):**
```hcl
# Reference the app subnet for Container Apps
app_subnet_id = module.landing_zone.subnet_ids["snet-app"]

# Reference the DB subnet for PostgreSQL private endpoint
db_subnet_id = module.landing_zone.subnet_ids["snet-db-private"]
```

### Network Security Groups (NSGs)

| Output Key | Description | Type |
|------------|-------------|------|
| `nsg_ids` | Map: subnet name → NSG ID | `map(string)` |
| `nsg_names` | Map: subnet name → NSG name | `map(string)` |

**NSG Rules (deny-by-default):**
- Allow intra-VNet traffic (VNet CIDR)
- Allow Azure Monitor / Log Analytics egress
- Allow Key Vault service tag egress (443)
- Deny all other ingress/egress (explicit deny)

**Usage (KB-047):**
```yaml
# NetworkPolicy reference (Kubernetes CNI)
# NSG enforces pod-to-pod isolation at the Azure layer
nsg_db_id: module.landing_zone.nsg_ids["snet-db-private"]
```

### Azure Firewall

| Output Key | Description | Type |
|------------|-------------|------|
| `firewall_id` | Firewall resource ID | `string` |
| `firewall_name` | Firewall name | `string` |
| `firewall_private_ip` | Private IP (UDR next-hop) | `string` |
| `firewall_public_ip` | Public IP (threat intel egress) | `string` |
| `route_table_id` | Route table forcing egress | `string` |

**Usage (KB-053):**
```hcl
# Force all egress through firewall for audit logging
route_table_id = module.landing_zone.firewall_route_table_id
next_hop_ip    = module.landing_zone.firewall_private_ip
```

---

## Key Vault and Customer-Managed Keys (CMK)

### Key Vault Coordinates

| Output Key | Description | Type | Example |
|------------|-------------|------|---------|
| `key_vault_id` | Key Vault resource ID | `string` | `/subscriptions/.../Microsoft.KeyVault/vaults/kv-dev-sea-abc1` |
| `key_vault_name` | Key Vault name | `string` | `kv-dev-sea-abc1` |
| `key_vault_uri` | Vault URI (for secret access) | `string` | `https://kv-dev-sea-abc1.vault.azure.net/` |
| `managed_identity_principal_id` | MI principal ID (Crypto User) | `string` | (GUID) |

### Customer-Managed Key (CMK)

| Output Key | Description | Type |
|------------|-------------|------|
| `cmk_key_id` | Versioned key ID (for encryption binding) | `string` |
| `cmk_key_versionless_id` | Versionless key ID (rotation-safe) | `string` |

**Key Properties:**
- **Type:** RSA-HSM
- **Key Size:** 3072 bits
- **Rotation:** 90-day automatic rotation (versionless ID for seamless rotation)
- **Usage:** Encrypt PostgreSQL storage, Storage Account blobs, Service Bus

### Secret Naming Convention

**Contract:** Secrets follow the pattern `db/{env}/{role}` as documented in `docs/db-contracts.md`.

| Output Key | Secret Name | Purpose | Consumer |
|------------|-------------|---------|----------|
| `secret_names.db_admin` | `db/{env}/admin` | Migration/DDL role | Migration Job (KB-053) |
| `secret_names.db_app` | `db/{env}/postgres` | Application role | App pods (KB-047) |

**Usage (KB-047 — External Secrets Operator):**
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: postgres-credentials
spec:
  secretStoreRef:
    name: azure-keyvault
    kind: ClusterSecretStore
  target:
    name: postgres-credentials
    creationPolicy: Owner
  data:
    - secretKey: host
      remoteRef:
        key: db/dev/postgres
        property: host
    - secretKey: username
      remoteRef:
        key: db/dev/postgres
        property: username
    - secretKey: password
      remoteRef:
        key: db/dev/postgres
        property: password
```

**Usage (KB-053 — PostgreSQL secret creation):**
```hcl
resource "azurerm_key_vault_secret" "db_admin" {
  name         = "db/${var.environment}/admin"
  value        = jsonencode({
    host     = azurerm_postgresql_flexible_server.main.fqdn
    port     = 5432
    username = "pgadmin"
    password = random_password.pg_admin.result
    dbname   = "postgres"
  })
  key_vault_id = module.landing_zone.key_vault_id
}
```

---

## Private Endpoints

| Output Key | Description | Type |
|------------|-------------|------|
| `private_endpoint_ids` | Map: endpoint name → resource ID | `map(string)` |
| `private_endpoint_ips` | Map: endpoint name → private IP | `map(string)` |
| `private_dns_zone_ids` | Map: DNS zone key → zone resource ID | `map(string)` |

**Pre-configured Private DNS Zones:**
- `postgres` — `privatelink.postgres.database.azure.com`
- `keyvault` — `privatelink.vaultcore.azure.net`
- `blob` — `privatelink.blob.core.windows.net`
- `servicebus` — `privatelink.servicebus.windows.net`

**Usage (KB-053):**
```hcl
# PostgreSQL private endpoint (created by KB-053, DNS zone pre-configured)
resource "azurerm_private_endpoint" "postgres" {
  name                = "pe-postgres-${var.environment}"
  location            = var.location
  resource_group_name = module.landing_zone.resource_group_name
  subnet_id           = module.landing_zone.subnet_ids["snet-pe-private"]

  private_service_connection {
    name                           = "psc-postgres"
    private_connection_resource_id = azurerm_postgresql_flexible_server.main.id
    subresource_names              = ["postgresqlServer"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "dns-postgres"
    private_dns_zone_ids = [module.landing_zone.private_dns_zone_ids["postgres"]]
  }
}
```

---

## Downstream Integration Examples

### KB-053: PostgreSQL with Private Endpoint and CMK

```hcl
module "landing_zone" {
  source = "../landing_zone" # or remote module source
  environment = var.environment
  location    = "southeastasia"
  tags        = var.tags
}

# PostgreSQL Flexible Server (private-only, CMK-encrypted)
resource "azurerm_postgresql_flexible_server" "main" {
  name                = "pg-${var.environment}-sea"
  resource_group_name = module.landing_zone.resource_group_name
  location            = module.landing_zone.location
  version             = "15"
  delegated_subnet_id = module.landing_zone.subnet_ids["snet-db-private"]
  private_dns_zone_id = module.landing_zone.private_dns_zone_ids["postgres"]
  sku_name            = "GP_Standard_D4ds_v4"
  storage_mb          = 131072

  customer_managed_key {
    key_vault_key_id = module.landing_zone.cmk_key_versionless_id
    primary_key_identity {
      object_id = module.landing_zone.managed_identity_principal_id
    }
  }

  high_availability {
    mode = "ZoneRedundant"
  }

  tags = module.landing_zone.tags
}

# Private endpoint (DNS zone already linked by landing zone)
resource "azurerm_private_endpoint" "postgres" {
  # ... as shown above ...
}
```

### KB-047: Kubernetes Secret Wiring

```yaml
# ClusterSecretStore (Azure Key Vault)
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: azure-keyvault
spec:
  provider:
    azurekv:
      vaultUrl: "https://kv-dev-sea-abc1.vault.azure.net/" # from key_vault_uri
      authType: WorkloadIdentity
      tenantId: "<tenant-id>"

# Application Secret (consumes db/{env}/postgres from Key Vault)
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-db-credentials
  namespace: default
spec:
  secretStoreRef:
    name: azure-keyvault
    kind: ClusterSecretStore
  target:
    name: app-db-credentials
    creationPolicy: Owner
  data:
    - secretKey: DATABASE_URL
      remoteRef:
        key: db/dev/postgres
        property: host
        # Construct full connection string in app config
```

---

## Terraform Module Usage

### Root Composition (example)

```hcl
terraform {
  required_version = ">= 1.5.0"
  backend "azurerm" {
    resource_group_name   = "rg-tfstate-dev-southeastasia"
    storage_account_name  = "sttfstatedevsea"
    container_name        = "tfstate"
    key                   = "landingzone.dev.tfstate"
    use_azuread_auth      = true
  }
}

provider "azurerm" {
  features {}
  skip_provider_registration = true
  use_oidc_auth = true
}

module "landing_zone" {
  source = "./terraform"

  environment = "dev"
  location    = "southeastasia"
  tags = {
    managed-by   = "terraform"
    pdpa-scope   = "true"
    environment  = "dev"
  }
}

# Outputs for downstream consumption
output "vnet_id" {
  value = module.landing_zone.vnet_id
}

output "subnet_ids" {
  value = module.landing_zone.subnet_ids
}

output "key_vault_uri" {
  value = module.landing_zone.key_vault_uri
}

output "cmk_key_versionless_id" {
  value = module.landing_zone.cmk_key_versionless_id
}
```

---

## Security and Compliance Checklist

- [x] **PDPA 2024:** All resources in `southeastasia` (Azure Malaysia)
- [x] **Network Isolation:** VNet segmentation with private subnets
- [x] **Private Endpoints:** No public exposure for PaaS services
- [x] **Azure Firewall:** Forced egress with threat intelligence (Alert mode)
- [x] **NSGs:** Deny-by-default with explicit allow rules
- [x] **Key Vault:** Customer-managed keys (RSA-HSM 3072) with 90-day rotation
- [x] **Secret Naming:** `db/{env}/{role}` convention for PostgreSQL credentials
- [x] **Remote State:** Per-environment state isolation in Azure Storage
- [x] **Tags:** `managed-by=terraform`, `pdpa-scope=true`, `environment={env}`

---

## Troubleshooting

### State Lock Conflicts

```bash
# Force unlock (only if certain no concurrent apply is running)
terraform force-unlock <LOCK_ID>
```

### Missing Private DNS Resolution

Ensure private endpoints are created and DNS zone virtual network links are active:

```bash
az network private-endpoint show \
  --name pe-postgres-dev \
  --resource-group rg-landing-zone-dev-southeastasia \
  --query 'privateDnsZoneConfigs[*].privateDnsZoneId'
```

### Key Vault Access Denied

Verify the managed identity has `Key Vault Crypto User` role assignment:

```bash
az role assignment list \
  --assignee <managed-identity-principal-id> \
  --scope <key-vault-id> \
  --query "[?roleDefinitionName=='Key Vault Crypto User']"
```

---

## Version History

| Version | Date | Change | Author |
|---------|------|--------|--------|
| 1.0 | 2026-10-29 | Initial contract (all modules complete) | Cloud Engineer |

---

**Next Steps:**
1. KB-053 consumes this contract to provision PostgreSQL, Storage, Service Bus, and Container Apps
2. KB-047 consumes this contract to wire Kubernetes secrets and network policies
3. Terraform state is initialized per-environment using the backend coordinates above
