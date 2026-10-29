# SRE Foundation CI Quality Gates

## Purpose
Define five CI quality gates that prevent unsafe SRE changes from merging. Each gate has pass/fail semantics and documented failure handling.

## Scope
SRE Foundation slice under mission M-MVKTMUFU-000V-OQTS (Malaysia Accounting SaaS Core Foundation).

## CI Quality Gate: 1 - Dependency CVE Scan

### Stage: `install`
### Tool/Command
`npm audit --audit-level=high`

### Pass Criteria
- No HIGH severity vulnerabilities
- No CRITICAL severity vulnerabilities
- Exit code 0

### Failure Handling
- Build fails if HIGH or CRITICAL vulnerabilities detected
- PR cannot merge until vulnerabilities are resolved or waived
- Waiver requires: Security Lead approval, documented risk assessment, timeline for remediation

## CI Quality Gate: 2 - Lint + Static Analysis

### Stage: `lint`
### Tool/Command
`npm run lint` (ESLint + TypeScript strict mode)

### Pass Criteria
- Zero ESLint errors
- Zero TypeScript compilation errors
- Exit code 0

### Failure Handling
- Build fails on any lint error
- PR cannot merge until errors are fixed
- Waiver requires: SRE Lead approval, documented rationale, and mitigation plan

## CI Quality Gate: 3 - SLO Burn-Rate Validation

### Stage: `test`
### Tool/Command
`tools/sre/validate-slo-burnrate.mjs`

### Description
Reads `docs/sre/slos.md` and `docs/sre/error-budgets.md`, asserts burn-rate thresholds (2×, 5×) are defined and numeric.

### Pass Criteria
- Burn-rate thresholds are defined for all configured SLAs
- Thresholds are numeric values
- 2× burn-rate alert configured and active
- 5× burn-rate alert configured and active

### Failure Handling
- Test fails if thresholds undefined or non-numeric
- PR cannot merge until burn-rate configuration is valid
- Waiver requires: SRE Lead approval and documented business exception

## CI Quality Gate: 4 - Runbook Lint

### Stage: `test`
### Tool/Command
`tools/sre/lint-runbooks.mjs`

### Description
Validates every file in `docs/sre/runbooks/` against runbook template requirements.

### Pass Criteria
- All runbooks have required front-matter fields
- All runbooks have required sections
- Verification status is one of: ✅, directional, knowledge-based
- Compliance regime is one of: PDPA, LHDN, SST, Payroll, None
- Last reviewed date within cadence

### Failure Handling
- Test fails if runbooks don't comply with template
- PR cannot merge until runbooks are corrected
- Waiver requires: SRE Lead approval and documented exception

## CI Quality Gate: 5 - Deployment Safety Checks

### Stage: `pre-deploy`
### Tool/Command
`tools/sre/validate-deployment-safety.mjs`

### Description
Asserts canary config, feature-flag registry, expand/contract migration pattern, rollback <30s, chaos schedule.

### Pass Criteria
- Canary deployment configuration present
- Feature-flag registry up to date
- Migration follows expand/contract pattern
- Rollback time target < 30 seconds verified
- Chaos engineering experiment schedule documented

### Failure Handling
- Gate fails if any requirement unmet
- Deployment blocked until safety checks pass
- Waiver requires: SRE Lead + Security Lead approval and rollback plan

## Pipeline Integration Notes

### Gate Ordering
Gates execute in sequence: install → lint → test → pre-deploy
Each gate must pass before the next stage begins.

### Required vs Optional
- Required gates: ALL five gates must pass
- Optional gates: Can be configured as project-level settings with defaults

### How to Waive
Waivers must be documented in the PR description with:
1. Gate being waived
2. Business justification
3. SRE Lead approval (explicit @ mention)
4. Security approval (for security-related gates)
5. Timeline for remediation
6. Risk acceptance documented

### Waiver Audit
All waivers are recorded in PR audit log and referenced in docs/sre/standards/waive-log.md

## References
- Mission M-MVKTMUFU-000V-OQTS (Malaysia Accounting SaaS Core Foundation)
- KB-023 (Observability Stack)
- KB-024 (SLOs & Error Budgets)
- KB-026 (Incident Response & Runbooks)
- KB-028 (Production Readiness & Deployment Safety)