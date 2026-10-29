# SRE Foundation Code Review Checklist

**Version:** 0.1
**Date:** 2026-10-24
**Author:** Code Quality Specialist (agent-560bd0bb)
**Status:** Draft — pending review
**Slice:** SRE Foundation (SL-MVMVNSSE-000T-46G5)
**Features:** Observability Stack (F-MVMVPFDT-000U-YQXJ), SLOs & Error Budgets (F-MVMVQ386-000W-UO4G), Incident Response & Runbooks (F-MVMVQXWY-000Y-QTHC), Production Readiness & Deployment Safety (F-MVMVR642-0010-QGUH)

---

This checklist extends the project-wide PR Review Checklist (`docs/quality/pr-review-checklist.md`) with SRE Foundation specific concerns. Every PR touching SRE Foundation code paths must satisfy both checklists.

## Operationalising the SRE Foundation Invariants

Use this checklist to evaluate every PR. Mark each item ✅ if satisfied, ❌ if not, or 📝 with a comment if a waiver is needed. A single ❌ in a **Restricted** category blocks merge until resolved.

---

### 1. Observability Instrumentation (Restricted)

- [ ] **Structured JSON logging** — All services emit structured JSON logs with `correlation_id`, `tenant_id`, `user_id` (hashed) per KB-023 AC.
- [ ] **No PII in logs** — Zero tokens, TINs, payroll records, or MyInvois tokens in any log line (extends invariant #5 from general checklist).
- [ ] **Metrics on `/metrics`** — Prometheus exposition format; includes request latency, error rate, throughput, business KPIs per KB-023 AC.
- [ ] **Tenant labels on all metrics** — Every metric carries `tenant_id` label for multi-tenant isolation.
- [ ] **Distributed trace propagation** — OpenTelemetry context propagated across service boundaries; `traceparent` header forwarded on all outbound calls.
- [ ] **Auto-instrumentation verified** — OpenTelemetry sidecar/operator injects instrumentation; manual spans only for business-critical operations.

### 2. SLO & Error Budget Discipline (Restricted)

- [ ] **SLO definitions committed** — SLOs defined for: e-Invois API uptime (99.5%), auth uptime (99.9%), general API (99.5%) per KB-024 AC.
- [ ] **Error budget calculations present** — Burn rate alerts configured at 2x and 5x thresholds per KB-024 AC.
- [ ] **SLO breach → postmortem** — Monthly SLO review documented; SLO breaches trigger postmortem process per KB-024 AC.
- [ ] **SLI measurement code reviewed** — SLI measurement logic (latency buckets, error counting) is deterministic and tested.
- [ ] **No ambient time in SLO logic** — Time windows for SLO calculation use injected clock, not `new Date()` (extends invariant #6 from general checklist).

### 3. Incident Response & Runbook Readiness (Restricted)

- [ ] **Runbooks exist for critical scenarios** — Documented runbooks for: e-Invois API outage, auth failure, RLS bypass, data breach, PDPA request, deployment rollback per KB-026 AC.
- [ ] **Runbook executable** — Runbook steps are concrete, automatable where possible, and tested in drills.
- [ ] **On-call escalation configured** — PagerDuty/Opsgenie rotation with escalation policies per KB-026 AC.
- [ ] **Severity levels defined** — SEV-1 to SEV-4 with clear criteria and response times per KB-026 AC.
- [ ] **Runbook linked from code** — Code that triggers alerts references the runbook URL in comments/annotations.

### 4. Production Readiness & Deployment Safety (Restricted)

- [ ] **Canary deployment pipeline** — Automated metric comparison between canary and baseline per KB-028 AC.
- [ ] **Feature flags for all new functionality** — Rollback <30s via flag toggle per KB-028 AC.
- [ ] **Database migrations follow expand/contract** — Zero-downtime migrations; no `DROP COLUMN` without expand phase per KB-028 AC.
- [ ] **Chaos engineering integration** — Monthly experiment results documented; no production impact per KB-028 AC.
- [ ] **Rollback tested** — Rollback procedure exercised in staging within last 30 days.

### 5. Tenant Isolation in Observability (Restricted)

- [ ] **Tenant-scoped metrics** — No cross-tenant metric aggregation in dashboards/alerts without explicit opt-in.
- [ ] **Tenant-scoped traces** — Trace queries filtered by `tenant_id`; no global trace search without authorization.
- [ ] **Tenant-scoped logs** — Log queries default to request-scoped tenant; admin override requires audit trail.

### 6. Determinism & Idempotency in SRE Paths (Restricted)

- [ ] **Alert evaluation deterministic** — Same metric series produces identical alert state; no flaky alerts.
- [ ] **Runbook automation idempotent** — Re-running automation steps (e.g., rollback, failover) is safe.
- [ ] **SLO calculation idempotent** — Re-computing SLO for same window produces byte-identical result.

### 7. Audit Trail for SRE Mutations (Restricted)

- [ ] **Config changes audited** — Alert rule changes, dashboard changes, runbook edits all produce audit entries.
- [ ] **Deployment metadata recorded** — Every deployment emits audit event with actor, tenant (system), timestamp, artifact SHA.
- [ ] **Feature flag changes audited** — Flag toggles produce audit entries with before/after state.

---

## Additional SRE Foundation Review Items

- [ ] **OpenAPI 3.1 for observability endpoints** — `/metrics`, `/health`, `/ready` endpoints documented with schemas.
- [ ] **Runbook markdown follows template** — Uses `docs/templates/runbook-template.md` (see Documentation Standards).
- [ ] **ADR for architectural decisions** — New observability stack choices, SLO changes, runbook architecture documented via ADR.
- [ ] **Dashboard-as-code** — Grafana dashboards version-controlled (Jsonnet/Helm); no click-ops dashboards in production.
- [ ] **Alert-as-code** — PrometheusRule / Alertmanager configs version-controlled; no manual alert creation in production.
- [ ] **Cost attribution** — Observability stack costs attributable per tenant (log volume, metric cardinality, trace sampling).

---

## Waiver Process

Same as general checklist (see `docs/quality/pr-review-checklist.md` §Waiver Process). Waivers tracked in `docs/quality/sre-pr-waivers.md`.

---

## Quick Reference: SRE Foundation AC Mapping

| Feature | Key AC Reference | Checklist Sections |
|---|---|---|
| Observability Stack (KB-023) | Structured logs, `/metrics`, traces, tenant labels | 1, 5 |
| SLOs & Error Budgets (KB-024) | SLO definitions, burn rate alerts, monthly review, postmortem | 2 |
| Incident Response (KB-026) | Runbooks, on-call, severity levels | 3 |
| Production Readiness (KB-028) | Canary, feature flags, expand/contract migrations, chaos | 4 |