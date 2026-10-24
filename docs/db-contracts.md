# Database Contracts — Multi-Tenant PostgreSQL Data Layer

Owner: Database Engineer (agent-dcc4da7f)
Feature: F-MVIJX7YF-000P-WGRJ (ACCO-007) — Multi-tenant PostgreSQL with PITR
Slice: SL-MVIJWY6P-000I-YT9V — Multi-tenant PostgreSQL data layer
Mission: M-MVIJWNII-0005-29TQ — Infrastructure foundation for Malaysia Accounting SaaS

Consumers:
- Kubernetes Engineer (agent-d609c639) — ACCO-010 K8s runtime (probe + secret wiring)
- JVM Engineer (agent-3b2f3c1c) — ACCO-020 application-layer tenant isolation
- Test Engineer (agent-e270b070) — ACCO-040 / ACCO-041 isolation test harness
- QA Lead (agent-34863834) — KB-018 Multi-tenant Kernel & Auth test strategy and plan (tenant isolation fixtures, RLS bypass tests)

Data residency: all customer data, backups and replicas stay in AWS ap-southeast-1 (PDPA 2024).
No cross-region replication of customer data.

---

## Part 1 — DB Connectivity Contract (for ACCO-010 / Kubernetes Engineer)

The *contract* is settled now. The *values* (endpoint hostname, exact Secrets Manager key
names, RDS CA bundle reference) land with ACCO-004 (Cloud Engineer, agent-15622fbc).
Consume those from ACCO-004 task notes — do not guess endpoints or re-derive the network.

### 1. Endpoint and port

- Managed **Amazon RDS for PostgreSQL** in ap-southeast-1. Not in-cluster DNS for the
  canonical path — RDS is the system of record.
- **Per environment**: dev / staging / prod each get their own RDS instance or cluster.
  Isolation between environments is enforced by separate VPC subnets and security groups
  from ACCO-004, not by sharing one instance.
- Standard PostgreSQL port `5432`.
- The app talks to **PgBouncer** (see §4), not to RDS directly.

### 2. Secrets Manager keys

Naming convention (exact names confirmed by ACCO-004):

```
db/{env}/postgres
```

JSON payload fields inside the secret:

| Field      | Meaning                                        |
|------------|------------------------------------------------|
| `host`     | RDS endpoint hostname (or PgBouncer Service DNS) |
| `port`     | `6432` for PgBouncer, `5432` for direct RDS     |
| `username` | application role name (see §5)                  |
| `password` | application role password                      |
| `dbname`   | application database name                      |

Wire via External Secrets Operator / Secrets Store CSI. Never hardcode credentials or
endpoints in manifests, ConfigMaps, or Helm values.

Two distinct secrets, not one blob:

- `db/{env}/postgres` — connection material for the app role.
- `db/{env}/admin` — migration/DDL role. Used only by the migration Job (§6), never by
  the running application pods.

### 3. TLS

- **TLS required**, minimum TLS 1.2. `sslmode=require` is the floor; use
  `sslmode=verify-full` with the RDS CA bundle for prod.
- The **RDS CA bundle** is mounted into pods as a **ConfigMap** (it is public trust
  material, not a secret). Mount path: `/etc/ssl/certs/rds-ca-bundle.pem`.
  The exact bundle reference is published by ACCO-004 with the RDS cluster.
- PgBouncer terminates the client-side TLS leg and opens its own TLS leg to RDS.

### 4. PgBouncer (ACCO-007 AC5)

- **Yes**, PgBouncer is in scope and required by ACCO-007 AC5.
- Runs **in-cluster** as a Deployment + Service. The app points `DATABASE_URL` at the
  PgBouncer Service DNS on port `6432`.
- PgBouncer config (`pgbouncer.ini`) is owned by the Database Engineer; the Kubernetes
  manifest is owned by the Kubernetes Engineer.
- Default sizing (tune per environment once ACCO-004 sizes the subnets):

  ```ini
  [databases]
  app = host=<rds-endpoint> port=5432 dbname=app

  [pgbouncer]
  listen_port = 6432
  pool_mode = transaction
  max_client_conn = 1000
  default_pool_size = 25
  reserve_pool_size = 5
  reserve_pool_timeout = 3
  server_reset_query = DISCARD ALL
  server_reset_query_always = 0
  ```

- `pool_mode = transaction` is required for RLS `SET LOCAL` semantics to be correct
  (see Part 2). `server_reset_query = DISCARD ALL` guarantees no tenant context leaks
  between transactions on a pooled server connection.

### 5. Readiness / liveness contract (ACCO-010 AC3)

- **Readiness**: `SELECT 1` — confirmed valid. The application DB role is limited
  privilege (no DDL, no superuser), so `SELECT 1` always succeeds.
- **Liveness**: process-only. A database blip **must not** restart pods — restarts put
  the legally-mandated LHDN filing path at risk.
- Run the readiness probe against the **PgBouncer port (6432)**, not directly against RDS.
  Probing RDS through the pooler means a pooler-side problem is visible to the app
  readiness gate rather than silently degrading latency.
- Budget: **< 500 ms p99**, probe `timeoutSeconds: 2`, `periodSeconds: 10`,
  `failureThreshold: 3`.

### 6. Migrations

- Migrations are owned by the **Database Engineer**; the runbook ships with ACCO-007 AC5
  and must be repeatable and reversible.
- Migrations run as a **separate step** — a dedicated K8s Job (template owned by the
  Kubernetes Engineer) or an external pipeline stage. The application pod **must not** run
  migrations on deploy.
- Concurrency is controlled by an advisory lock plus a `schema_migrations` version table,
  so a racing deploy cannot double-apply.
- Recommended sequence on deploy: `migrate Job completes → app rollout`.
- Migration tool choice (Flyway/Liquibase vs. plain SQL + version table) is published in
  ACCO-007 notes when the slice is picked up.

### 7. Out of scope for ACCO-010

Backup CronJobs, snapshot/PITR configuration, restore drills, RPO/RTO runbooks, and
encryption-at-rest / retention policy remain with the Database Engineer under ACCO-007.
Postgres backups are explicitly **not** an ACCO-010 concern.

---

## Part 2 — Tenant Isolation / RLS Contract (for ACCO-020)

### The problem

ACCO-007 AC2 requires tenant isolation **enforced at the database level**, with automated
tests proving no cross-tenant leakage. App-layer filters alone do not satisfy acceptance.
Cross-tenant leakage is the highest-severity defect class for this platform (PDPA 2024,
multi-client firm workspaces).

### Isolation model: shared schema + RLS

Firm-edition workspaces hold many client entities. **Per-tenant schema** would mean
thousands of schemas with unbounded migration fan-out and impossible connection pooling;
per-tenant database would break the pooler economics and the restore drill. Chosen model:

> **Shared schema, shared tables, `tenant_id` discriminator column, PostgreSQL Row Level
> Security enforced on every tenant-scoped table.**

### Tenant context: `SET LOCAL` in a transaction (the contract)

**Decision: per-request transaction setting via `SET LOCAL`, not a session variable.**

- `SET LOCAL` is scoped to the enclosing transaction and is **automatically reset on
  commit or rollback**. A session variable (`SET app.tenant_id`) persists on a pooled
  connection and is the classic source of cross-tenant leakage — one forgotten reset
  exposes one firm's data to another.
- `SET LOCAL` requires the app to run each unit of work inside an explicit transaction
  that sets tenant context **first**. This is a deliberate contract the app layer must
  honour, and it makes "transaction or nothing" the safe default.
- Requires PgBouncer `pool_mode = transaction` (§4) and `server_reset_query = DISCARD ALL`
  as a belt-and-braces second line of defence.

### Exact contract the application layer must satisfy

The application sets tenant context **as the first statement of every transaction**, on
the same connection that will run the query:

```sql
BEGIN;
SET LOCAL app.tenant_id = '<uuid>';   -- first statement, every transaction
-- ... application queries ...
COMMIT;
```

Through PgBouncer in transaction pooling mode this is a single round trip:

```
BEGIN;
SET LOCAL app.tenant_id = '…';
SELECT …;
COMMIT;
```

Required properties:

1. `SET LOCAL app.tenant_id` is the **first** statement in every transaction touching a
   tenant-scoped table.
2. The tenant id is always a **bound parameter**, never string-interpolated.
3. If tenant context is not set, the transaction must **fail closed** — see below.
4. A tenant id is never settable by end users; it is derived server-side from the
   authenticated session and the requested client entity, and validated against the
   workspace membership before being sent to the database.

### Fail-closed behaviour (no tenant context = no rows)

Every tenant-scoped table gets a policy of this shape:

```sql
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON invoices
  USING      (tenant_id = current_setting('app.tenant_id', true)::uuid)
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
```

- `current_setting('app.tenant_id', true)` returns `NULL` when unset — the `missing_ok`
  form. `NULL = tenant_id` evaluates to NULL, and NULL is **not** true, so the policy
  denies. This is the fail-closed default: **no tenant context means no rows returned and
  no writes accepted.**
- `FORCE ROW LEVEL SECURITY` ensures the policy applies to the table owner as well, so
  migrations and maintenance paths cannot bypass it by accident.
- Every tenant-scoped table must have both `ENABLE` and `FORCE` RLS, and a policy on
  `USING` and `WITH CHECK`. `WITH CHECK` is what stops a tenant from *writing* a row
  stamped with another tenant's id.

### Session variable fallback (documented, not recommended)

If the JVM Engineer needs session-scoped context for a specific non-transactional path
(a background worker with a single tenant, for example), the supported form is:

```sql
SET app.tenant_id = '<uuid>';   -- session-scoped, MUST be reset
```

with a mandatory `RESET app.tenant_id` in a `finally` block, and such a connection must
**not** be returned to the pool with the variable still set. This path is an exception,
not the default, and every use must be reviewed.

### Roles

| Role          | Used by                     | Rights                                              |
|---------------|-----------------------------|-----------------------------------------------------|
| `app`         | Next.js API, filing worker  | CRUD on tenant-scoped tables, no DDL, no BYPASSRLS   |
| `migrator`    | Migration Job only          | DDL, schema ownership; never used by app pods       |
| `reporting`   | Reporting/analytics only    | `SELECT` on approved views; RLS still applies       |

No application role gets `BYPASSRLS` or `SUPERUSER`. The `app` role must **not** own the
tenant-scoped tables — ownership plus `FORCE ROW LEVEL SECURITY` is what makes the
policy unbypassable in practice.

### What the isolation harness (ACCO-040 / ACCO-041, Test Engineer) can rely on

- With tenant A set, `SELECT` on any tenant-scoped table returns **zero** rows of tenant
  B.
- With tenant A set, an `INSERT`/`UPDATE` stamped with tenant B's id is **rejected** by
  `WITH CHECK`.
- With **no** tenant context set, reads return **zero rows** and writes are **rejected**.
- The app role cannot read the underlying tables bypassing the policy (no `BYPASSRLS`).
- The harness should **fail loudly** if RLS is missing or misconfigured. If it finds RLS
  disabled on a tenant-scoped table, that is a **finding**, not something to work around.
- The harness must exercise the real `app` role, not a superuser — a superuser bypasses
  RLS and would produce false passes.

### Open item for JVM Engineer + Test Engineer

Confirm before implementation closes:
1. Does the JVM Engineer's persistence layer guarantee every query runs inside an
   explicit transaction (so `SET LOCAL` is always in scope)? If some paths run
   auto-commit statements, we must fall back to the session-variable form with mandatory
   `RESET`, and the harness must cover that path too.
2. Confirm the tenant id type is `uuid` end to end (policy casts to `::uuid`).

Next owner: JVM Engineer (agent-3b2f3c1c) + Database Engineer (agent-dcc4da7f) jointly on
ACCO-020; Test Engineer (agent-e270b070) on ACCO-040 / ACCO-041; QA Lead (agent-e6e797c8)
signs off the attestation.
