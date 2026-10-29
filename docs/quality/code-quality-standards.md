# Code Quality Standards

**Version:** 0.1  
**Date:** 2026-10-23  
**Author:** Code Quality Specialist (agent-560bd0bb)  
**Status:** Draft — pending review

## Scope & Principles

- **Fail‑loud** — Never warn‑only for Restricted‑class patterns; every violation must be a CI-blocking error.
- **Config‑as‑code** — All linting/static‑analysis configuration lives in version‑controlled files (`.eslintrc`, `phpstan.neon`, `ruff.toml`, etc.), not inline or generated at runtime.
- **Version‑pinned tools** — Tooling versions are pinned in `package.json` / `composer.json` and updated via explicit dependency bumps, never implicit resolution.

## Linting Rule Categories

### Correctness

| Rule | Rationale |
|---|---|
| `null`/`undefined` checks | Prevent runtime crashes in financial computation paths |
| `typeof` guards before-operations | Ensure math operations receive validated operands |
| `===` / `!==` over `==` / `!=` | Eliminate type‑coercion bugs |

### Style

| Rule | Rationale |
|---|---|
| Consistent naming (camelCase for variables, PascalCase for components) | Team readability across languages |
| Line-length limit (100 chars) | CI readability; overrides allowed with comment justification |
| Quote style (single quotes for strings, template literals for multi‑line) | Diff noise reduction |

### Security

| Rule | Rationale |
|---|---|
| **No hard‑coded secrets** — `process.env`, secret‑manager, or CI injects only | Prevents credential leakage in repos |
| **No `console.log` of sensitive data** (tokens, TINs, payroll records) | Audit‑trail safety; MyInvois tokens are 60‑min, never logged |
| **Sanitize all external inputs** before they reach compliance‑significant code paths | Defends against injection attacks on filing pipelines |

### Financial Invariants (Non‑Negotiable)

| Rule | Rationale | Enforcement |
|---|---|---|
| **Decimal‑cents as integers** for all MYR amounts | Floating‑point rounding errors destroy financial accuracy | CI must block `float`/`double`/`number` for monetary fields; require `decimal(18,4)` in Postgres or integer‑cents in code |
| **Explicit rounding per document type** — never rely on implicit rounding | Tax rounding ≠ line rounding; LHDN gazette rules vary | Provide named rounding functions (`roundToCents`, `roundToLine`) with documented rounding mode |
| **Versioned lookup tables** for SST rates, EPF/SOCSO/EIS/HRD/PCB thresholds | Rates change with LHDN/IRB/EPF gazette notices; must be auditable as‑of a date | Store thresholds in a `compliance_rates` table with `effective_from` date; code queries by date, never hard‑codes |
| **No `new Date()` buried in tax/compliance logic** | Temporal correctness — logic must be as‑of‑dated | Inject `effectiveDate` as a parameter; forbid `new Date()` in pure compliance functions |
| **Determinism** — same inputs produce byte‑identical output | e-Invois `documentHash` is SHA‑256 over the document; nondeterminism breaks submission | Pure functions only; all randomness/non‑determinism isolated in adapter layer; property‑based tests enforce |
| **Idempotency** — duplicate‑detection and resubmission paths must not double‑post | MyInvois rejects duplicates; a retry must be safe | Retry logic must check `documentHash` already‑submitted; CI test verifies idempotent resubmission |

### Tenant Isolation

| Rule | Rationale |
|---|---|
| **No ambient tenant** — every data access must derive tenant scope from explicit request‑scoped context | Firm‑edition multi‑client code must carr ry tenant ID explicitly through the call chain; no global/tracking tenant context |
| **Tenant‑scoped queries only** — `WHERE tenant_id = :requestTenant` on all data operations | Prevents cross‑client data leakage |

### Temporal Correctness

| Rule | Rationale |
|---|---|
| **No `new Date()` in tax/compliance logic** | Tax logic is as‑of‑dated; injecting `new Date()` breaks auditability |
| **Inject effective date** as a parameter to all compliance functions | Makes time-dependence explicit and test‑friendly |

### Determinism & Idempotency

- **Pure functions** for document hashing and financial math
- **Retry‑safe submission paths** — idempotent by design (documentHash as primary key)

### Audit Trail

- **Every Restricted/Confidential mutation** must have an append‑only audit write in the same transaction boundary
- **Audit entries** must include: actor, tenant, timestamp, before/after state
- **Financial data is evidence‑grade** — cannot be silently overwritten

## Static Analysis Policy

| Language | Required Tool | Minimum Severity | CI Gate |
|---|---|---|---|
| TypeScript / JavaScript | ESLint + TSDoc | Error for Restricted‑class rules | Block on any error |
| Python | Ruff + mypy | Error for Restricted‑class rules | Block on any error |
| PHP | PHPStan | Error for Restricted‑class rules | Block on any error |

- **Severity mapping:** Rule category → error (blocking) / warning (allowed to pass with comment)
- **Restricted‑class rules** (secrets, PII, financial invariants, tenant isolation) must always be **error** severity — never warning‑only.
- CI must **fail** the pipeline on any Restricted‑class error.

## Coverage & Testing Expectations

| Artifact | Requirement |
|---|---|
| Unit tests for pure logic | 100% branch coverage on functions that implement financial invariants |
| Property‑based tests for financial math | QuickCheck‑style tests asserting determinism, idempotency, and rounding correctness |
| Integration tests for filing paths | End‑to‑end mock of MyInvois submission; verify idempotent retry paths |
| Golden‑set eval for any AI surface | Reference data per `docs/data‑ai‑strategy.md` §6; precision floors and regression gate |

## Deferred Language‑Specific Configs (must cross‑link)

| Config | Owner | Target File |
|---|---|---|
| ESLint/TSDoc rules for Next.js/TypeScript | TypeScript Engineer (agent-0e13d730) | `.eslintrc` + `docs/quality/code-quality-standards.md` |
| PHPStan rules for PHP | PHP Backend Engineer (agent-ffa682cd) | `phpstan.neon` + `docs/quality/code-quality-standards.md` |

Both deferred configs must reference this document and ensure their rule sets are compatible with the language‑agnostic policy authored here.