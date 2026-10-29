# Helm Chart: Malaysia Accounting SaaS

This Helm chart defines the Kubernetes runtime for the Malaysia Accounting SaaS, covering the web UI, API, e-Invois filing worker, and in-cluster PgBouncer connection pooler.

## Chart Structure

```
infra/kubernetes/
├── Chart.yaml                    # Chart metadata
├── values.yaml                   # Default values
├── values-dev.yaml               # Dev environment overrides
├── values-staging.yaml           # Staging environment overrides
├── values-prod.yaml              # Production environment overrides
└── templates/                    # Kubernetes manifests
    ├── _helpers.tpl              # Template helpers
    ├── deployment-*.yaml         # Deployments (api, web, worker, pgbouncer)
    ├── service-*.yaml            # Services
    ├── configmap-*.yaml          # ConfigMaps (PgBouncer config, RDS CA bundle)
    ├── serviceaccount.yaml       # IRSA ServiceAccount
    ├── clustersecretstore.yaml   # External Secrets Operator ClusterSecretStore
    ├── externalsecret.yaml       # External Secrets for DB credentials
    ├── hpa-*.yaml                # HorizontalPodAutoscalers
    ├── scaledobject-*.yaml       # KEDA ScaledObjects
    ├── poddisruptionbudget.yaml  # PodDisruptionBudgets
    └── networkpolicy.yaml        # NetworkPolicies
```

## Environments

The chart supports three environments with distinct values files:

| Environment | Values File | HPA Min | HPA Max | TLS Mode | PDB |
|-------------|-------------|---------|---------|----------|-----|
| Dev | `values-dev.yaml` | 1 | 2 | `require` | Yes |
| Staging | `values-staging.yaml` | 2 | 4 | `require` | Yes |
| Prod | `values-prod.yaml` | 3 | 12 | `verify-full` | Yes |

## Installation

### Dev Environment

```bash
helm install dev . -f values-dev.yaml
```

### Staging Environment

```bash
helm install staging . -f values-staging.yaml
```

### Production Environment

```bash
helm install prod . -f values-prod.yaml
```

## Pre-Deployment Checklist

Before deploying to any environment, ensure the Cloud Engineer (ACCO-004) has provided:

- [ ] Concrete subnet IDs (`PLACEHOLDER_SUBNET_IDS_*`)
- [ ] Security group IDs (`PLACEHOLDER_SG_IDS_*`)
- [ ] EKS endpoint (`PLACEHOLDER_EKS_ENDPOINT_*`)
- [ ] IRSA role ARNs (`PLACEHOLDER_*_IRSA_ROLE_ARN`)
- [ ] RDS CA bundle content (`PLACEHOLDER_RDS_CA_BUNDLE_*`)
- [ ] RDS endpoint for PgBouncer database config

## Health Probes

### API (port 4000)
- **Liveness**: `GET /api/healthz` — process health only, never hits DB
- **Readiness**: `GET /api/readyz` — `SELECT 1` through PgBouncer (port 6432)

### Filing Worker (port 8080)
- **Liveness**: `GET /healthz` — process health only
- **Readiness**: `GET /readyz` — `SELECT 1` through PgBouncer (port 6432)

### PgBouncer (port 6432)
- Connects app pods to RDS PostgreSQL via in-cluster connection pooling

## Autoscaling

- **CPU-based**: HPA scales based on CPU utilization (70% target)
- **Event-based**: KEDA scales API on HTTP request rate, worker on queue depth
- **Zero available**: Dev worker can scale to zero when idle

## Security

- **RBAC**: All containers run as non-root (UID 1000)
- **Seccomp**: RuntimeDefault profile enforced
- **TLS**: Minimum TLS 1.2, verify-full in prod
- **Secrets**: Injected at runtime via External Secrets Operator from AWS Secrets Manager
- **Network**: Egress limited to DNS, PgBouncer, and LHDN endpoints

## Migration Jobs

Migrations run as separate Kubernetes Jobs using the `db/{env}/admin` secret.
They use advisory locks and a `schema_migrations` table to prevent concurrent execution.

Run before rolling out new app versions:

```bash
helm upgrade <release> . --set migration.run=true
```

## Compliance

This chart enforces:

- **PDPA 2024**: All data in `ap-southeast-1`, backups not in scope of ACCO-010
- **Zero dropped requests**: Rolling update with `maxUnavailable: 0`
- **Filing worker resilience**: Minimum replica floor for single-node loss survival