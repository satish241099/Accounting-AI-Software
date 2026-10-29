# SRE Foundation Code Review Checklist

## Purpose
Define seven SRE invariants and waive process for the SRE Foundation slice (Observability Stack, SLOs, Incident Response, Production Readiness). Ensures PRs meet SRE-specific quality standards before merging.

## Scope
SRE Foundation slice under mission M-MVKTMUFU-000V-OQTS (Malaysia Accounting SaaS Core Foundation).

## Waiver Process
Waivers require:
- SRE Lead approval
- Security approval
- Waiver must be documented in PR description with business justification and timeline
- Recorded in docs/sre/standards/code-review-checklist.md waive-log.md

## Invariants

### 1. Determinism & Idempotency
**Rationale:** All SRE code (observability, metrics, incident response, deployment safety) must be deterministic and idempotent to ensure safe retries and predictable behavior in production.

**Detection Method:** Automated tests validate deterministic execution; manual review checks for random or time-dependent code.

**Waiver Criteria:** Only when there's no alternative implementation path, approved for high-complexity systems only.

### 2. Audit Trail
**Rationale:** Every SRE action that mutates state (alert rules, runbooks, SLOs, feature flags, migrations) must emit an audit event with actor, before/after state, and correlation_id for forensic analysis.

**Detection Method:** Automated audit log tests validate actor attribution; manual review verifies audit event structure.

**Waiver Criteria:** Only for read-only SRE configurations, documented with explicit risk acceptance.

### 3. Explicit Tenant Context
**Rationale:** SRE code must never infer tenant information; must receive `tenant_id` via correlation context to enforce zero-trust isolation.

**Detection Method:** Static analysis scans for hardcoded tenant assumptions; automated tests validate context propagation.

**Waiver Criteria:** Only for system-level SRE code with no tenant data, requiring explicit documentation of risk.

### 4. No Token/PII Logging
**Rationale:** Extend global logging standards to SRE code to prevent accidental logging of tokens, NRIC, bank accounts, or financial data in observability systems.

**Detection Method:** Automated log redaction tests; manual review for any explicit PII in logs, metrics, or traces.

**Waiver Criteria:** Only when no alternative observability approach exists, with explicit data masking and audit requirements.

### 5. As-Of-Dated Compliance Logic
**Rationale:** All SLO/error-budget/runbook logic referencing LHDN/PDPA thresholds must be versioned and as-of-dated to ensure traceability of regulatory requirements.

**Detection Method:** Automated date checks on regulatory references; manual review of temporal logic in compliance code.

**Waiver Criteria:** Only when referencing static regulatory requirements with documented expiration tracking.

### 6. Fail-Loud on SRE Guardrails
**Rationale:** SRE guardrails (SLO burn-rate, runbook lint, deployment safety checks) must block merge failures, not warn, to ensure safe SRE changes.

**Detection Method:** Automated CI failure verification; manual review confirms guardrail failures are non-overrideable.

**Waiver Criteria:** Only for emergency cases, with SRE Lead approval and clear rollback plan.

### 7. Observability Completeness
**Rationale:** New/changed services must emit structured logs, metrics, and traces per KB-023 schema to ensure full observability coverage.

**Detection Method:** Automated schema validation; manual review confirms all required observability components.

**Waiver Criteria:** Only for small-scope services where observability requirements are explicitly documented and accepted.

## PR Review Checklist

| Requirement | ✅ Pass | ❌ Fail | N/A | Notes |
|-------------|---------|--------|-----|-------|
| **Invariant 1** Determinism & Idempotency | | | | |
| **Invariant 2** Audit Trail | | | | |
| **Invariant 3** Explicit Tenant Context | | | | |
| **Invariant 4** No Token/PII Logging | | | | |
| **Invariant 5** As-Of-Dated Compliance Logic | | | | |
| **Invariant 6** Fail-Loud on SRE Guardrails | | | | |
| **Invariant 7** Observability Completeness | | | | |
| **SLO Burn-Rate Thresholds Defined** | | | | |
| **Runbook Compliance Metadata Present** | | | | |
| **Deployment Safety Checklist Included** | | | | |

## Required Checklist Items
- All seven invariants documented in PR description
- Automation test coverage for invariants implemented
- Waivers documented with business justification and timeline
- Actor and correlation_id captured in audit logs
- All observability components implemented per KB-023 schema
- Compliance logic referenced with as-of-dated compliance metadata
- Guardrail failures block merge (not warn)
- Explicit tenant context propagation verified
- No PII/token logging in production code
- Automated tests passing in CI pipeline

## Review Process
1. Automated CI runs: Dependency CVE Scan, Lint+Static Analysis, SLO Burn-Rate Validation, Runbook Lint, Deployment Safety Checks
2. Manual review validates all seven invariants based on code changes
3. Waiver approvals documented in PR description
4. All guardrail checks pass before merge

## Contacts
- SRE Lead: Not specified
- Security Lead: Not specified
- Emergency Waivers: Use channel #sre-emergencies

## References
- Mission M-MVKTMUFU-000V-OQTS (Malaysia Accounting SaaS Core Foundation)
- KB-023 (Observability Stack)
- KB-024 (SLOs & Error Budgets)
- KB-026 (Incident Response & Runbooks)
- KB-028 (Production Readiness & Deployment Safety)