# CI Quality Gates

**Version:** 0.1  
**Date:** 2026-10-23  
**Author:** Code Quality Specialist (agent-560bd0bb)  
**Status:** Draft — pending review

## Gate Definitions

Each gate is evaluated in the CI pipeline. A gate that **fails** blocks the pipeline (fails‑loud). Every gate has a failure mode caught, an implementation approach, the pipeline stage at which it runs, and pass/fail semantics.

| # | Gate | Purpose | Failure Mode Caught | Implementation Approach | Pipeline Stage | Pass/Fail Semantics |
|---|---|---|---|---|---|---|
| 1 | **Dependency CVE Scan** | Detect known vulnerabilities in project dependencies | Any high‑severity CVE in `package.json` / `composer.json` / `requirements.txt` | `npm audit` (Node) / `snyk` / `pip-audit` / `php depend` | `pull_request` & `push` to `main` | **Fail** on any `high` severity; `medium` is warning‑only with comment |
| 2 | **Lint + Static Analysis** | Enforce language‑agnostic quality policy and per‑language rules | Any Restricted‑class rule violation (secrets, PII, financial invariants, tenant isolation) | ESLint + TSDoc (TS), Ruff + mypy (Python), PHPStan (PHP); severity = error for Restricted‑class | `pull_request` & `push` to `main` | **Fail** on any Restricted‑class error; other warnings allowed with `// review-ignored` comment |
| 3 | **Financial Math Property‑Based Tests** | Verify determinism, idempotency, and rounding correctness | Test failure in `test/validate-standards.sh` or property‑based test suite | Shell script (`test/validate-standards.sh`) runs unit/property tests; golden‑set eval for AI surfaces | `pull_request` & `push` to `main` | **Fail** on any test error/failure |
| 4 | **OpenAPI Schema Validation** | Ensure every HTTP endpoint & MyInvois‑facing call has a valid OpenAPI 3.1 entry | Missing or malformed OpenAPI entry for a handler | `spectral` or `swagger-cli` validation against `.openapi/` directory | `pull_request` | **Fail** on validation errors |
| 5 | **Docstring Coverage** | Verify public functions carry required docstring fields | Public function missing JSDoc/TSDoc, Google‑style, or PHPDoc fields | Custom script parsing source files against convention checklist | `pull_request` | **Fail** if any public function lacks required docstring fields |

## Pipeline Stage Order (recommended)

1. **Dependency CVE Scan** — fastest fail, blocks on high CVEs
2. **Lint + Static Analysis** — enforces quality policy
3. **Financial Math Property‑Based Tests** — verifies invariants
4. **OpenAPI Schema Validation** — contract compliance
5. **Docstring Coverage** — documentation completeness

## Gate Failure Handling

- **Fail‑loud** — Every Restricted‑class violation surfaces as a visible CI error, never swallowed.
- **Warning‑only gates** (e.g., `medium` severity CVEs) produce a comment on the PR but do not block merge; the author must acknowledge or address.
- **Gate bypass** is policy‑gated: only via `fn_task_bypass_review` escape hatch for a stranded in‑review task, not for CI gates.