# PR Review Checklist

**Version:** 0.1  
**Date:** 2026-10-23  
**Author:** Code Quality Specialist (agent-560bd0bb)  
**Status:** Draft — pending review

## Operationalising the Seven Compliance Invariants

Use this checklist to evaluate every PR. Mark each item ✅ if satisfied, ❌ if not, or 📝 with a comment if a waiver is needed. A single ❌ in a **Restricted** category blocks merge until resolved.

### 1. Determinism
- [ ] Pure functions for document hashing and financial math are verified (property‑based tests pass).
- [ ] No hidden state or non‑deterministic calls (`Math.random()`, `new Date()`, system timestamps) in compliance‑critical paths.
- [ ] CI property‑based test suite passes without failure.

### 2. Idempotency
- [ ] Retry/submission paths are idempotent — `documentHash` check prevents double‑post.
- [ ] MyInvois duplicate‑rejection is handled gracefully (retry produces same outcome or explicit `already-submitted` state).
- [ ] No code path that could post the same filing twice without a guard.

### 3. Audit Trail
- [ ] Every Restricted/Confidential mutation has an append‑only audit write in the same transaction boundary.
- [ ] Audit entries include: **actor**, **tenant**, **timestamp**, **before/after** state.
- [ ] Financial data changes are traceable to an actor+tenant+timestamp tuple.

### 4. Explicit Tenant Context
- [ ] No ambient tenant — every data access derives tenant scope from explicit request‑scoped context.
- [ ] All queries have `WHERE tenant_id = :requestTenant` (or equivalent) — verified via code review.
- [ ] Tenant‑isolation test harness (ACCO-041) passes for the changed code path.

### 5. No Token / PII Logging
- [ ] No MyInvois 60‑min tokens, TINs, or payroll records appear in `console.log`, error messages, or analytics payloads.
- [ ] Secrets are sourced from `process.env` / secret manager, never hard‑coded.
- [ ] A secret‑scan run (ESLint rule, `npm audit --audit-level=high`, or `detect-secrets`) passes clean.

### 6. As‑of‑Dated Tax Logic
- [ ] No `new Date()` buried in tax/compliance logic.
- [ ] `effectiveDate` is injected as a parameter to all compliance functions.
- [ ] Tax logic is verified against a fixed effective date in unit tests.

### 7. Fail‑Loud on Compliance
- [ ] Any violation of invariants 1‑6 is a CI‑blocking error (fail‑loud), not a warning‑only.
- [ ] Restricted‑class rule errors never receive `// review-ignored` without explicit owner approval.
- [ ] The PR description references the relevant invariant number(s) and the call‑to‑action for resolution.

## Additional Review Items

- [ ] OpenAPI 3.1 entry exists for every new/changed HTTP endpoint / MyInvois‑facing call.
- [ ] Docstrings follow the convention for the language (JSDoc/TSDoc, Google‑style Python, PHPDoc PHP).
- [ ] Module header declares compliance regime, authoritative source, and verification status (✅/directional/knowledge‑based).
- [ ] Financial amounts use **decimal‑cents as integers** — no `float`/`double`/`number` for MYR.
- [ ] Version‑pinned tools (ESLint, PHPStan, mypy) are respected; no implicit resolution.
- [ ] Deprecated/no‑longer-maintained code paths are flagged and either removed or documented.

## Waiver Process

If any item is marked ❌ and a waiver is required:

1. The PR author must document the waiver in the PR description, referencing the invariant number and the risk acceptance.
2. The waiver must be **explicitly approved** by the QA Lead (agent-34863834) or the Code Quality Specialist (agent-560bd0bb).
3. Waived items are tracked in a `docs/quality/pr-waivers.md` log (created when first needed).
4. Waivers are time‑boxed — reassessed at the next milestone boundary.