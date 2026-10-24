# Tenant Isolation — Test Plan

**Task:** ACCO-041 (QA component of ACCO-016)
**Author:** Test Engineer (agent-e270b070)
**Created:** 2026-10-22
**Status:** Draft — DevOps contract received 2026-10-22 (agent-b1697565), QA Lead de-risking notes received, pending ACCO-016 scope coordination & CI skeleton land
**Contract Source:** `docs/db-contracts.md` Part 2 (Database Engineer, agent-dcc4da7f)
**Related Test Strategy:** `docs/test-strategy/multi-tenant-kernel-auth.md` (KB-018 — Multi-tenant Kernel & Authentication slice)

---

## 1. Scope

This plan covers the **QA/test** component of tenant isolation for the Malaysia Accounting SaaS
multi-tenant firm edition. It defines every cross-tenant leakage vector the harness must prove
closed, the assertions that must hold, and the CI gate contract.

**Out of scope:**
- Application-layer tenant context implementation (ACCO-020 / JVM Engineer).
- Schema creation or migration authoring (ACCO-007 / Database Engineer, ACCO-016).
- Filing-worker or background-job tenant scoping (later features).

---

## 2. Threat Model & Isolation Guarantee

| Threat | Vector | What must NOT happen |
|--------|--------|---------------------|
| Cross-tenant SELECT | Read any tenant-scoped table with tenant A context | Zero rows of tenant B returned |
| Cross-tenant INSERT | Write to tenant-scoped table with tenant A context, stamp tenant B id | Rejected by `WITH CHECK` |
| Cross-tenant UPDATE | Update row owned by tenant B while tenant A context is set | No rows affected |
| Cross-tenant DELETE | Delete rows owned by tenant B while tenant A context is set | No rows affected |
| No-context read | Query with no tenant context set | Zero rows returned (fail-closed) |
| No-context write | Write with no tenant context set | Rejected |
| Superuser bypass | Test as superuser instead of `app` role | Must NOT be used — produces false passes |
| Missing RLS | RLS not enabled/forced on a tenant-scoped table | Harness raises a **FINDING**, does not skip |
| Session variable leak | `SET app.tenant_id` without `RESET` on pooled conn | Covered if JVM Engineer reports auto-commit paths |

---

## 3. Database Contract Summary

Per `docs/db-contracts.md` Part 2:

- **Model:** Shared schema, shared tables, `tenant_id uuid` discriminator, Postgres RLS on every tenant-scoped table.
- **Tenant context:** `SET LOCAL app.tenant_id = $1` — first statement of every transaction.
- **Policy shape:**
  ```sql
  ALTER TABLE <table> ENABLE ROW LEVEL SECURITY;
  ALTER TABLE <table> FORCE ROW LEVEL SECURITY;
  CREATE POLICY tenant_isolation ON <table>
    USING      (tenant_id = current_setting('app.tenant_id', true)::uuid)
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
  ```
- **Fail-closed:** `current_setting('app.tenant_id', true)` returns `NULL` when unset → `NULL = tenant_id` is `NULL` (not true) → policy denies.
- **Roles:** `app` role (no DDL, no BYPASSRLS), `migrator` role (DDL only, never used by app), `reporting` role (SELECT only, RLS still applies).
- **PgBouncer:** `pool_mode = transaction`, `server_reset_query = DISCARD ALL`.

---

## 4. Harness Requirements

### 4.1 Must use real `app` role
The harness connects as the `app` role, NOT a superuser. A superuser bypasses RLS and produces
false passes. If the `app` role does not exist yet, the harness reports a FINDING and fails.

### 4.2 Must use `missing_ok` variant
Policies use `current_setting('app.tenant_id', true)::uuid`. The harness validates this
behaviour: unset context → NULL → not true → fail-closed.

### 4.3 Fail loudly, never skip
If RLS is disabled or misconfigured on any tenant-scoped table, the harness:
1. Records a **FINDING** (table name, RLS enabled status, policy presence).
2. Returns failure (exit code ≠ 0).
3. Does NOT silently pass or skip the table.

### 4.4 Cover session-variable fallback path
If the JVM Engineer confirms auto-commit paths exist (open question 1 in db-contracts.md),
the harness must also exercise `SET app.tenant_id` + mandatory `RESET` path.

---

## 5. Test Entities & Coverage

The harness targets every **tenant-scoped table** in the schema. At time of writing, the
schema has not been implemented (no SQL files in the repo). The harness discovers tenant-scoped
tables dynamically and validates each one.

### 5.1 Tenant-Scoped Tables (Expected)

Based on the domain (Malaysia accounting SaaS, multi-tenant firm edition), the following
entity categories are expected to be tenant-scoped:

| Category | Expected Tables |
|----------|----------------|
| Core identity | `tenants`, `clients`, `users`, `roles`, `firm_profiles` |
| Chart of accounts | `accounts`, `account_types`, `journal_entries`, `journal_lines` |
| Invoicing | `invoices`, `invoice_lines`, `invoice_statuses`, `credit_notes` |
| Payments | `payments`, `payment_methods`, `bank_accounts`, `bank_transactions` |
| Tax | `tax_rates`, `tax_transactions`, `sst_declarations` |
| e-Invois | `e_invoices`, `e_invoice_submissions`, `e_invoice_responses` |
| Payroll | `employees`, `payroll_periods`, `payroll_items`, `statutory_contributions` |
| Audit | `access_logs`, `audit_trails`, `compliance_events` |
| Files | `file_uploads`, `file_metadata` |
| Settings | `firm_settings`, `client_settings`, `tax_configurations` |

**Dynamic discovery:** The harness queries `information_schema.tables` joined against
`pg_class.relpersistence` to discover all tables in the `public` schema, then checks:
1. Does the table have a `tenant_id` column of type `uuid`?
2. Is RLS enabled (`pg_class.relrowsecurity`)?
3. Is RLS forced (`pg_class.relforcerowsecurity`)?
4. Is there a policy matching the expected shape?

Any table with a `tenant_id` column that does NOT have RLS enabled+forced is a **FINDING**.

### 5.2 File/Blob Access Path

File uploads are expected to be stored externally (S3) with tenant-scoped key prefixes.
The harness validates:
1. File metadata tables have RLS policies.
2. File access URLs contain tenant-scoped paths (cannot be shared).
3. Cross-tenant file access attempts return 403/404.

---

## 6. Test Cases

### 6.1 Read Isolation

For each tenant-scoped table:

```
GIVEN: tenant A and tenant B exist, table T has rows for both tenants
WHEN:  SET LOCAL app.tenant_id = tenant_A_uuid
THEN:  SELECT * FROM T returns ONLY rows where tenant_id = tenant_A_uuid
AND:   Zero rows where tenant_id = tenant_B_uuid
```

### 6.2 Write Isolation (INSERT)

For each tenant-scoped table:

```
GIVEN: tenant A context is set
WHEN:  INSERT INTO T (..., tenant_id = tenant_B_uuid, ...)
THEN:  INSERT is rejected (WITH CHECK policy violation)
AND:   No rows are written
```

### 6.3 Write Isolation (UPDATE)

For each tenant-scoped table:

```
GIVEN: tenant A context is set, tenant B owns row R
WHEN:  UPDATE T SET ... WHERE id = R.id
THEN:  UPDATE affects 0 rows
AND:   Row R is unchanged
```

### 6.4 Write Isolation (DELETE)

For each tenant-scoped table:

```
GIVEN: tenant A context is set, tenant B owns row R
WHEN:  DELETE FROM T WHERE id = R.id
THEN:  DELETE affects 0 rows
AND:   Row R still exists
```

### 6.5 No-Context Fail-Closed

```
GIVEN: No tenant context is set (no SET LOCAL)
WHEN:  SELECT * FROM any_tenant_scoped_table
THEN:  Zero rows returned

GIVEN: No tenant context is set
WHEN:  INSERT INTO any_tenant_scoped_table
THEN:  INSERT is rejected
```

### 6.6 RLS Policy Audit

For every table in the `public` schema:

```
GIVEN: Table T
WHEN:  Check pg_class.relrowsecurity and pg_class.relforcerowsecurity
THEN:  If T has a tenant_id column, both flags must be TRUE
AND:   If a policy is missing, raise a FINDING
```

### 6.7 Aggregation Isolation

For tables that support aggregation (COUNT, SUM, AVG):

```
GIVEN: tenant A context is set
WHEN:  SELECT COUNT(*), SUM(amount) FROM tenant_scoped_table
THEN:  Aggregation includes ONLY tenant A's rows
AND:   tenant B's rows are NOT counted or summed
```

### 6.8 Cross-Tenant Reference Integrity

```
GIVEN: parent table P and child table C, both tenant-scoped
WHEN:  Query JOIN P JOIN C with tenant A context
THEN:  Only tenant A's parent-child relationships are returned
AND:   tenant B's related rows are not accessible
```

---

## 7. CI Gate Contract (Deliverable #3)

### 7.1 Integration Pattern

The isolation test suite must run as a required check in the CI/CD pipeline (ACCO-033).

**Pending DevOps coordination** (message sent to DevOps Lead agent-b1697565):
- Job name and placement in pipeline
- Required check registration on branch protection rules
- Artifact retention for attestation reports
- Database provisioning (test DB with RLS)

### 7.2 Block Conditions

The CI gate must **block merge** when:
1. Any isolation test fails.
2. RLS is not enabled+forced on any tenant-scoped table.
3. The harness cannot connect as the `app` role.

The CI gate must **NOT skip** the suite. If the schema doesn't exist yet, the harness fails
loudly with a clear message (not a skip).

### 7.3 Attestation Artifact (Deliverable #4)

Per-run output:
- **JUnit XML** for CI result display.
- **JSON attestation report** containing:
  - Timestamp (UTC ISO 8601)
  - Commit SHA and branch
  - List of tables checked
  - Per-table result: pass/fail/finding
  - RLS policy audit summary
  - Overall verdict: PASS / FAIL / FINDINGS

The attestation report is retained for PDPA 2024 audit.

---

## 8. Implementation Notes

### 8.1 Harness Technology

The harness uses **Python + pytest + psycopg** because:
- Stack-agnostic (talks SQL directly to Postgres, independent of app framework).
- Runs in CI as a container (`testcontainers` or `pg_isready` + external test DB).
- Python engineers are available (agent-456700e4, agent-8d2e1933).
- pytest produces JUnit XML natively.

### 8.2 Database Setup

The harness needs:
1. A test Postgres instance (local or CI-provisioned).
2. The `app` role created (no superuser, no BYPASSRLS).
3. The schema applied (migrations from ACCO-007/ACCO-016).
4. Seed data for 2+ tenants with rows in every tenant-scoped table.

Until the schema exists, the harness:
1. Reports a **FINDING**: "Schema not applied — no tenant-scoped tables found."
2. Returns exit code 1 (failure, not skip).

### 8.3 Session Variable Fallback

If JVM Engineer confirms auto-commit paths:
- The harness exercises `SET app.tenant_id = $1` (session-scoped).
- After each test, verifies `RESET app.tenant_id` was called.
- A leaked session variable is a **FINDING**.

---

## 9. Open Questions

| # | Question | Owner | Status |
|---|----------|-------|--------|
| 1 | Does JVM Engineer's persistence layer guarantee every query runs in an explicit transaction? | agent-3b2f3c1c | Open (db-contracts.md) |
| 2 | CI pipeline structure and required-check contract for ACCO-033 | agent-b1697565 / agent-67d92bf7 | Message sent 2026-10-22 |
| 3 | Artifact retention policy for attestation reports (where stored, how long) | agent-b1697565 | Pending DevOps reply |
| 4 | Tenant ID type confirmation (uuid end-to-end) | agent-3b2f3c1c + agent-dcc4da7f | Open (db-contracts.md) |

---

## 10. Deliverable Status

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | Documented test plan | ✅ This document |
| 2 | Automated test suite | In progress — harness spec complete, code pending schema |
| 3 | CI wiring | Pending DevOps coordination (ACCO-033) |
| 4 | Attestation artifact format | Defined (JUnit XML + JSON report) |
| 5 | RLS validation | BLOCKED — no schema/migrations in repo yet (ACCO-007/ACCO-016) |

---

## 11. Findings

### FINDING-001: No Schema or Migrations Present

**Severity:** HIGH (blocks deliverable #5)

The repository contains no SQL files, no migrations, and no application code.
Row Level Security cannot be validated because:
- No tenant-scoped tables exist.
- No `app` role has been created.
- No RLS policies have been applied.

The harness will report this as a failure (not a skip) until the schema lands.

**Raised to:** QA Lead (agent-e6e797c8), Database Engineer (agent-dcc4da7f)
**Depends on:** ACCO-007 (PostgreSQL), ACCO-016 (Tenant isolation enforcement), ACCO-013 (Firm workspace)

---

*End of test plan.*
