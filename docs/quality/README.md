# Code Quality & Documentation Standards

**Version:** 0.1  
**Date:** 2026-10-23  
**Author:** Code Quality Specialist (agent-560bd0bb)  
**Status:** Draft — pending review

## Index of Standards Documents

| Document | Purpose | Owner |
|---|---|---|
| [`code-quality-standards.md`](/docs/quality/code-quality-standards.md) | Language‑agnostic linting, static analysis, and compliance invariants | Code Quality Specialist |
| [`documentation-conventions.md`](/docs/quality/documentation-conventions.md) | JSDoc/TSDoc, Python docstrings, PHPDoc, OpenAPI 3.1, module header convention | Code Quality Specialist |
| [`ci-quality-gates.md`](/docs/quality/ci-quality-gates.md) | CI gate definitions, pipeline stages, pass/fail semantics | Code Quality Specialist |
| [`pr-review-checklist.md`](/docs/quality/pr-review-checklist.md) | PR review checklist operationalising compliance invariants | Code Quality Specialist |

## Deferred Language‑Specific Configs

| Standard | Owner | Task |
|---|---|---|
| ESLint/TSDoc rules for Next.js/TypeScript | TypeScript Engineer (agent-0e13d730) | ACCO-088 |
| PHPStan rules for PHP | PHP Backend Engineer (agent-ffa682cd) | ACCO-086 |

Both deferred configs must cross-link their written standard into `docs/quality/code-quality-standards.md` and `docs/quality/ci-quality-gates.md` so the language‑agnostic policy and per‑language rules cannot drift apart.

---

*This index lives at the root of `docs/quality/`. All linked documents should be markdown files in the same directory.*