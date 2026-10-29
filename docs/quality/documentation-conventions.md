# Documentation Conventions

**Version:** 0.1  
**Date:** 2026-10-23  
**Author:** Code Quality Specialist (agent-560bd0bb)  
**Status:** Draft — pending review

## Module Header Convention

Every domain module must open with a header block that declares:

```markdown
# Module: <module-name>

- **Compliance Regime:** <regime-name> (e.g. MyInvois, SST, EPF, KS)
- **Authoritative Source:** <URL> (e.g. `sdk.myinvois.hasil.gov.my`, `kwsp.gov.my`)
- **Verification Status:** ✅ verified / directional / knowledge-based
  - Per `docs/competitive-analysis.md` §8 convention — extend it, don't invent a new one.
```

- The `✅ / directional / knowledge‑based` markers must appear **from day one** so the architecture/design doc inherits the discipline.
- `verified` = confirmed against the authoritative source; `directional` = known direction but not audited; `knowledge‑based` = inferred from docs/expertise, not verified.

## Docstring Standards

### TypeScript / JavaScript — JSDoc / TSDoc

Every public function carries:

```typescript
/**
 * One‑line purpose statement.
 *
 * @param {<type>} paramName - Description with units & currency if applicable.
 * @returns {{<field>: <type>}} Invariants on the returned value (compliance‑significant).
 * @throws {<ErrorType>} Failure modes that are compliance‑significant.
 */
```

- `@param` must include units and currency when money is involved.
- `@returns` must state the invariants (e.g. "returns decimal‑cents integer", "never null when input validated").
- `@throws` lists failure modes that would cause a filing to fail or produce incorrect SST amounts.

### Python — Google‑style docstrings

```python
"""
One-line purpose statement.

Args:
    param_name (Type): Description with units & currency if applicable.
Returns:
    Description of returned value invariants.
Raises:
    ExceptionType: Failure modes that are compliance‑significant.
"""
```

### PHP — PHPDoc

```php
/**
 * One-line purpose statement.
 *
 * @param mixed $paramName Description with units & currency if applicable.
 * @return mixed Invariants on the returned value (compliance‑significant).
 * @throws ExceptionType Failure modes that are compliance‑significant.
 */
```

## API Surface — OpenAPI 3.1

- **Every HTTP endpoint** and **every MyInvois‑facing call** gets an OpenAPI 3.1 entry.
- The spec lives **with the handler**, not in a separate wiki.
- Each entry includes: schema, error codes, idempotency behaviour, auth scope.
- Idempotency keys must be documented for all POST/PUT paths that MyInvois supports.

## Docs Hierarchy

| Layer | Content | Markers |
|---|---|---|
| `docs/` | Durable specs (architecture, compliance, ADRs) | Author/date/status header on every long‑form analysis |
| `docs/` | Long‑form analysis | Claims carry ✅/directional/knowledge‑based marker from day one |
| Project wiki / chat | Transient analysis | No guaranteed persistence; migrate to `docs/` for durability |

- Every **claim** in any durable doc must carry the ✅/directional/knowledge‑based marker from the first draft.
- When a claim is updated, the marker is revised to reflect the new confidence level.