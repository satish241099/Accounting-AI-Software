# SRE Foundation Documentation Standards

## Purpose
Define ADR and runbook templates with PDPA/LHDN compliance metadata, documentation hierarchy, and review cadence for the SRE Foundation slice.

## Scope
SRE Foundation slice under mission M-MVKTMUFU-000V-OQTS (Malaysia Accounting SaaS Core Foundation).

## ADR Template

### Front Matter
```yaml
---
id: ADR-XXX
title: Brief descriptive title
status: proposed | accepted | superseded
date: YYYY-MM-DD
deciders: Name1, Name2, Name3
compliance_regime: PDPA | LHDN | SST | Payroll | None
authoritative_source: https://example.com or docs/xxx.md
verification_status: ✅ | directional | knowledge-based
supersedes: ADR-YYY or None
tags: [tag1, tag2]
---
```

### Required Sections
1. **Context** — Background and problem statement
2. **Decision** — The architectural decision made
3. **Consequences** — Implications and trade-offs
4. **Compliance Impact** — PDPA/LHDN/SST/Payroll considerations
5. **Rollback Plan** — How to revert the decision
6. **Links** — Related documents and resources

## Runbook Template

### Front Matter
```yaml
---
id: RUNBOOK-XXX
title: Brief descriptive title
severity: SEV-1 | SEV-2 | SEV-3 | SEV-4
trigger: Condition that activates this runbook
detection: How this incident is detected
owner: Name or team responsible
compliance_regime: PDPA | LHDN | SST | Payroll | None
authoritative_source: https://example.com or docs/xxx.md
verification_status: ✅ | directional | knowledge-based
last_reviewed: YYYY-MM-DD
tags: [tag1, tag2]
---
```

### Required Sections
1. **Overview** — Summary of the incident scenario
2. **Prerequisites** — Required tools, access, and environment setup
3. **Detection** — How to identify the incident has occurred
4. **Mitigation Steps** — Step-by-step actions to contain the incident
5. **Recovery Verification** — How to confirm the incident is resolved
6. **Post-Actions** — Follow-up tasks and documentation updates
7. **Rollback** — Steps to revert to pre-incident state
8. **Links** — Related runbooks and resources

## Compliance Metadata Rules
- Every ADR and runbook must include all six front-matter fields: `id`, `title`, `status` (or `severity` for runbooks), `compliance_regime`, `authoritative_source`, `verification_status`
- Missing fields result in lint failure
- Compliance regime must be one of: PDPA, LHDN, SST, Payroll, None
- Verification status must be one of: ✅, directional, knowledge-based
- Authoritative source must be a verifiable URL or document reference
- Last reviewed date must be within 30 days for runbooks, 90 days for ADRs

## Documentation Hierarchy
- **ADRs:** `docs/sre/adrs/` — Naming: `ADR-XXX-*.md`
- **Runbooks:** `docs/sre/runbooks/` — Naming: `RUNBOOK-XXX-*.md`
- **Index:** `docs/sre/adrs/index.md` and `docs/sre/runbooks/index.md`
- **Standards:** `docs/sre/standards/` — This directory

## Review Cadence
- **ADRs:** Reviewed quarterly
- **Runbooks:** Reviewed monthly and after every incident
- **Compliance Documents:** Reviewed annually or when regulations change
- **Verification Status:** Updated when authoritative sources change

## Naming Convention
- ADRs: `ADR-XXX-description.md` where XXX is sequential
- Runbooks: `RUNBOOK-XXX-description.md` where XXX is sequential
- Standards: `standards-name.md`

## Required Index Files
- `docs/sre/adrs/index.md` — Lists all ADRs with status and links
- `docs/sre/runbooks/index.md` — Lists all runbooks with severity and links
- `docs/sre/standards/README.md` — Lists all standards with descriptions

## Verification Status Convention
- ✅ — Verified against authoritative source
- directional — Directional guidance based on best practices
- knowledge-based — Based on internal knowledge without authoritative verification

## References
- Mission M-MVKTMUFU-000V-OQTS (Malaysia Accounting SaaS Core Foundation)
- KB-023 (Observability Stack)
- KB-024 (SLOs & Error Budgets)
- KB-026 (Incident Response & Runbooks)
- KB-028 (Production Readiness & Deployment Safety)