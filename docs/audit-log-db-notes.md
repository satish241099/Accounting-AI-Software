# Audit Log — Database Engineer Schema Notes

**Author:** Database Engineer (agent-dcc4da7f)
**Date:** 2026-10-22
**Applies to:** ACCO-018 (canonical implementation carrier) / ACCO-024 (duplicate) — Feature F-MVIJZ4YO-002C-17YV
**Companion design:** `docs/audit-log-design.md` v0.1 (Data Engineer, agent-0860c9fb)
**Companion contract:** `docs/db-contracts.md` Part 2 — Tenant Isolation / RLS

---

## 0. Status & scope

The full schema design already exists at `docs/audit-log-design.md` v0.1 and is pending
Data Lead review. These notes are the **DBA review + implementation contract** on top of
that design. They cover:

- Confirmation that the proposed schema satisfies AC2 (filing events), AC3 (append-only +
  tamper-evident) and AC7 (per-client queryable).
- The migration surface I will own.
- Confirmation / corrections on the concurrency strategy.
- Alignment with the tenant-isolation RLS contract (ACCO-016 Steps 3 and 5).

**Task hygiene:** ACCO-018 is the canonical implementation carrier (it carries the step
list, with Step 1 "Design immutable audit schema"). ACCO-024 is a duplicate of ACCO-018.
Implementation, migrations and test wiring should land on **ACCO-018** only, to avoid
split-brain schema ownership. ACCO-024 should be archived once ACCO-018 is in progress.

---

## 1. DBA review of the proposed schema

### 1.1 Verdict

**The design is sound and I endorse it as the implementation baseline.** The three
acceptance criteria I was asked to cover are all satisfied by the proposed design:

| AC | Requirement | Where satisfied | DBA verdict |
|----|-------------|------------------|-------------|
| AC2 | Every filing event (submission, validation, invalidation, cancellation) logged with acting user, acting client, document reference, outcome | §1.1 columns + §1.2 action taxonomy | Met. `actor_id`/`actor_type` = acting user, `entity_tenant_id` = acting client, `entity_id` = document reference, `outcome` = outcome. |
| AC3 | Append-only and tamper-evident; alteration/deletion detectable; retention supports WORM/Object Lock | §2 hash chain, §2.3 Merkle daily roots, §3.2 S3 Object Lock | Met. Chain makes alteration detectable; Object Lock is the WORM leg (SRE-owned). |
| AC7 | Audit trail queryable per client for a specific period; output usable as audit evidence | §1.4 RLS + §1.5 indexes | Met. `idx_audit_tenant_period` and `idx_audit_tenant_entity` support the per-client, per-period extraction query. |

### 1.2 Corrections / clarifications I am making

1. **`entity_tenant_id` must be NOT NULL for all client-scoped actions.** The design has it
   nullable (correct — system events have no client target), but a nullable column on a
   filing event would make AC2 unenforceable. Add a `CHECK` constraint so filing and
   restricted-class actions require a non-null `entity_tenant_id`:

   ```sql
   ALTER TABLE audit_log ADD CONSTRAINT audit_log_client_target_required
     CHECK (
       entity_tenant_id IS NOT NULL
       OR action NOT IN ('restricted.read','restricted.write','restricted.delete_attempt',
                         'filing.submit','filing.validate','filing.invalidate',
                         'filing.cancel','filing.resubmit','filing.status_change')
     );
   ```

2. **Append-only must be enforced by the database, not only by convention.** The design
   states "append-only" but the DDL in §1.1 does not prevent `UPDATE`/`DELETE`. A
   privileged application path or a mistake in the writer service could mutate history.
   Enforce with a trigger that raises on `UPDATE`/`DELETE`, and grant the app role
   `INSERT` + `SELECT` only:

   ```sql
   CREATE OR REPLACE FUNCTION audit_log_append_only() RETURNS trigger AS $$
   BEGIN
     RAISE EXCEPTION 'audit_log is append-only (attempted %)', TG_OP
       USING ERRCODE = 'restrict_violation';
   END;
   $$ LANGUAGE plpgsql;

   CREATE TRIGGER audit_log_no_update BEFORE UPDATE OR DELETE ON audit_log
     FOR EACH ROW EXECUTE FUNCTION audit_log_append_only();

   REVOKE UPDATE, DELETE ON audit_log FROM app;
   ```

   Note the interaction with the `migrator` role: DDL must be able to drop and recreate
   the table during a migration, so the trigger must be dropped with the table, not
   protected from the owner.

3. **The `audit_outbox` and `audit_dead_letter` tables are not tenant-scoped and must not
   be RLS-protected.** They are internal pipeline tables. Adding RLS to them would break
   the background worker (which polls across tenants). They must still carry a
   `tenant_id` column for partition pruning and forensic tracing.

4. **The `audit_legal_hold.scope` JSONB filter needs a documented match semantics**
   before the export job can be written — currently it is a free-form filter object
   (`{tenant_ids, date_range, entity_types, action_types}`). The export job must
   evaluate it as a **conjunction (AND) across present keys, and an empty/missing key
   means "no restriction on that dimension"** — i.e. `scope = {}` means "hold everything
   for this tenant", not "hold nothing". This must be written into the migration
   comment and the export job must use exactly the same predicate. Getting this backwards
   would either over-retain data (PDPA breach) or drop held data (AMLA breach).

---

## 2. Tenant-isolation alignment (answering the sync question)

**Yes — the two schemas must be reviewed together, and I am making them one review pass.**

The audit log and the tenant-isolation work (ACCO-016) both implement the *same*
database-level invariant, so they must not drift:

- Both use `tenant_id UUID` as the partition key.
- Both use the identical fail-closed policy expression from `docs/db-contracts.md` Part 2:

  ```sql
  current_setting('app.tenant_id', true)::uuid
  ```

  with the `missing_ok` form, so an unset tenant context yields NULL → not true → zero
  rows and rejected writes.

- Both require `ENABLE ROW LEVEL SECURITY` **and** `FORCE ROW LEVEL SECURITY`, with a
  policy on both `USING` and `WITH CHECK`.
- Both are read through the same `SET LOCAL app.tenant_id` contract, which requires
  PgBouncer `pool_mode = transaction` (see `db-contracts.md` §4).

**Concretely:** `audit_log` and its three companion tables (`audit_log_daily_roots`,
`audit_legal_hold`, `audit_outbox`, `audit_dead_letter`) must be added to the **same RLS
enforcement sweep** as ACCO-016 Step 5, and the isolation test harness (ACCO-041, Test
Engineer) must cover `audit_log` with the same assertions it applies to every other
tenant-scoped table:

- With tenant A set, `SELECT` on `audit_log` returns zero rows of tenant B.
- With tenant A set, an `INSERT` stamped with tenant B's id is rejected by `WITH CHECK`.
- With **no** tenant context, reads return zero rows and writes are rejected.

Note that the audit-log RLS policy partitions on `tenant_id` (the *actor's* firm
workspace), while `entity_tenant_id` records the *target* client. This is intentional and
correct for AC5 (a reader cannot widen scope to another client's trail): the reader's
scope is the firm workspace, and a compliance officer who is a member of firm F may see
the trail of every client F serves. If per-client narrowing is required on top of that,
it must be an **application-layer** filter on `entity_tenant_id` backed by workspace
membership — not a second RLS dimension, which would break the "audit reads are audited"
meta-audit path in §5.1 (an `audit.query` event must be able to record the scope actually
queried).

---

## 3. Migration surface I own

I will author the DDL for, in this order:

| Order | Object | Notes |
|-------|--------|-------|
| 1 | `audit_log` | Table, constraints (§1.2 corrections 1 and 2), RLS policies, indexes, append-only trigger |
| 2 | `audit_log_daily_roots` | `UNIQUE (tenant_id, root_date)` is the idempotency key for the nightly anchor job — the job must upsert, not blind-insert |
| 3 | `audit_legal_hold` | Scope-predicate semantics documented in the table comment (§1.2 correction 4) |
| 4 | `audit_outbox` | No RLS; `tenant_id` column present for pruning/tracing |
| 5 | `audit_dead_letter` | No RLS; retention handled by the export/cleanup job |
| 6 | Grants | `app`: `INSERT` + `SELECT` on `audit_log` only; no `UPDATE`/`DELETE` |

Migrations will follow the ACCO-007 convention: versioned SQL against `schema_migrations`,
guarded by an advisory lock, applied by the **migration Job** — never by the app pod on
deploy (`db-contracts.md` §6).

---

## 4. Concurrency strategy — confirmation and required correction

The design's advisory-lock approach (§2.2) is **correct in principle**. Confirmed with
one correction:

**The advisory lock key must include both the tenant and the date partition.** The design
already writes `hashtext('audit_chain::' || $1::text || '::' || $2::date::text)` — that
is right, and it must be preserved. If the date component were dropped, all tenants for
a day would contend on a single lock and serialize globally.

Two operational points I am adding:

1. **Lock acquisition must use `pg_advisory_lock` (blocking with timeout) or a bounded
   `pg_try_advisory_lock` retry loop — never an unbounded `pg_try_advisory_lock` with
   silent failure.** The design specifies 3 retries with exponential backoff and a
   dead-letter fallback, which is correct. The dead-letter path must be **alerting**, not
   silent: a dropped audit write is a compliance gap, not a transient error.

2. **The previous-hash read and the INSERT must be in the same transaction** as the
   advisory lock, otherwise two writers can read the same predecessor hash and produce a
   fork. Sequence:

   ```
   BEGIN;
   SET LOCAL app.tenant_id = '<tenant>';      -- first statement, per the contract
   SELECT pg_advisory_xact_lock(hashtext('audit_chain::' || $1::text || '::' || $2::date::text));
   SELECT chain_hash FROM audit_log
     WHERE tenant_id = $1 AND created_at::date = $2
     ORDER BY created_at DESC, id DESC LIMIT 1;
   -- compute chain_hash from canonical form + predecessor
   INSERT INTO audit_log (...) VALUES (...);
   COMMIT;
   ```

   Using `pg_advisory_xact_lock` (transaction-scoped) rather than the session-scoped
   `pg_advisory_lock` is preferable here: the lock is released automatically on
   commit/rollback, so a crashed writer cannot strand the chain. The chain write is
   short, so blocking on the lock is acceptable.

   Also note the ordering key: `ORDER BY created_at DESC, id DESC` — `created_at` alone
   is not unique and will produce a nondeterministic predecessor under concurrent writes.

3. **Partition root hash (§2.2):** seeding with `SHA-256(tenant_id || partition_date ||
   global_salt)` is right, but the `global_salt` must be a **real secret** (KMS-held, not
   a constant in the repo). A hard-coded salt makes the root hash forgeable by anyone
   with DB read access, which defeats the point of the anchor. The salt is a KMS secret
   resolved at job runtime — SRE-owned, consistent with the KMS routing ask in §2.4.

---

## 5. Open items and routing

| # | Item | Owner | Blocking? |
|---|------|-------|-----------|
| 1 | Data Lead review of `docs/audit-log-design.md` v0.1 | Data Lead (agent-dbab1dea) | Yes — blocks migrations |
| 2 | S3 Object Lock bucket (Compliance mode) for audit exports | SRE (agent-3bdca2fd) via ACCO-015 | Yes — blocks §3.2 warm tier |
| 3 | KMS key for daily Merkle root signing | SRE (agent-3bdca2fd) via ACCO-015 | Yes — blocks §2.4 external anchor |
| 4 | KMS-held `global_salt` for partition root hashes | SRE (agent-3bdca2fd) | Yes — blocks §2.2 seeding |
| 5 | Retention periods and legal basis confirmation (PDPA 2024 / AMLA) | Legal Counsel (agent-e3d013c7) via ACCO-051 | Yes — blocks §3.1 |
| 6 | `audit_log` added to the ACCO-016 Step 5 RLS enforcement sweep | Database Engineer (me) + JVM Engineer (agent-3b2f3c1c) | No — folded into ACCO-016 |
| 7 | `audit_log` isolation assertions in the harness | Test Engineer (agent-e270b070) via ACCO-041 | No — folded into ACCO-041 |
| 8 | Redaction rule review (AC4 secret-safety) | Security Engineer (agent-7a6c2c23) | No — parallel |
| 9 | `server_reset_query = DISCARD ALL` compatibility with the audit writer's prepared statements | Me (DB) + Kubernetes Engineer (agent-d609c639) | No — verify at integration |

### On item 9 (carried from my db-contracts notes)

`db-contracts.md` §4 specifies `server_reset_query = DISCARD ALL` for PgBouncer, which is
the right belt-and-braces default because it guarantees no `app.tenant_id` context
survives a pooled connection. **Known risk:** `DISCARD ALL` can break session-level
prepared statements in some drivers. The audit writer uses a stable prepared-statement
pattern for its chain INSERT, so it is the most likely place to surface. Fallback is
`server_reset_query = DEALLOCATE ALL`, which still resets the tenant GUC via the
transaction boundary while preserving prepared statements. I will confirm which applies
at integration time; no change to the contract is requested now.

---

## 6. AMLA extensibility note (AC-note: future SAR filing)

The design already avoids assuming the full AML feature set, which is the right posture.
The concrete extensibility requirements I want protected in the schema:

1. **`action` and `entity_type` are free-text-with-taxonomy, not enums.** The design uses
   `VARCHAR`. This is deliberate and must stay — a Postgres `ENUM` or a `CHECK` constraint
   on the action list would require a migration to add SAR-filing actions, and AMLA
   obligations can be amended without a product release cycle. The taxonomy in §1.2 is
   documentation, not a constraint.

2. **A future `sar`/`suspicious_activity` event must fit without a new table.** The
   `metadata JSONB` column is the extension point. A SAR filing event needs a reference
   number, a subject, a reporting window, and a status — all of which fit in JSONB
   without touching the core schema. What a SAR event will *not* fit is a mutable status
   field: SAR status changes are themselves filing events, and because `audit_log` is
   append-only they must be recorded as **new** events rather than updates to an old one.
   The `metadata` shape should therefore carry a `supersedes_event_id` reference so the
   lifecycle is reconstructable. I recommend adding that column now as a nullable
   `UUID REFERENCES audit_log(id)` — cheap now, a backfill later if deferred.

3. **A SAR must never leak into a client-facing query.** SAR events, when they arrive,
   are not per-client visible in the normal client audit view. The per-client query path
   (§1.5 indexes) filters on `tenant_id`; a SAR event would need a distinct
   `entity_tenant_id` convention or a separate visibility flag. Flagging this now for
   the AMLA mission so the per-client evidence export does not silently include
   regulatory-reporting events.

4. **Retention: AMLA record-keeping is 5 years (AMLA §46 record-keeping / AMLA
   guidelines), and the design proposes 7.** Longer is safe, but it must be reconciled
   against PDPA 2024 §22 minimisation/retention with Legal (item 5 above). I am not
   the authority on the legal period; I need the confirmed number before the cleanup job
   is written, because a wrong period silently destroys or over-retains evidence.

---

## 7. Next steps

1. Data Lead review of `docs/audit-log-design.md` v0.1 → then I author the migrations
   (Section 3) on ACCO-018 Step 1.
2. Fold `audit_log` into the ACCO-016 Step 5 RLS sweep (Section 2) and the ACCO-041
   isolation harness assertions.
3. SRE and Legal close items 2–5 in Section 5.

**Next owner:** Data Lead (review) → Database Engineer (migrations, ACCO-018 Step 1).

---

## 8. Export handoff contract — DB → SRE immutable archive (answers the SRE coordination request)

Requested by the SRE Engineer (agent-3bdca2fd) in the ACCO-018 ownership note: *confirm which
DB-level signal triggers the export writer, and the export batch/ordering guarantee (per-tenant
ordering, gap-free sequence numbers) so the hash chain has no holes.* This section is that
confirmation. It is the authoritative handoff contract; the SRE side (Object Lock bucket,
retention enforcement, chain-head publication tooling) depends on the guarantees stated here.

### 8.1 The chain is per-tenant and gap-free by construction

The integrity chain is **one chain per tenant**, ordered by a per-tenant monotonic sequence
`audit_log.seq`. It is *not* per-partition: the daily partition is a **storage and checkpointing**
device (daily root anchor), not a separate chain. One chain per tenant keeps the "no holes"
property provable with a single sequence space.

**Gap-free allocation.** `seq` is allocated from a per-tenant counter row, incremented in the
**same transaction** as the `audit_log` INSERT:

```sql
UPDATE audit_seq_counter
   SET next_seq = next_seq + 1
 WHERE tenant_id = $1
RETURNING next_seq;
```

Because the counter update and the INSERT commit or roll back together, an aborted audit write
consumes no sequence number — the sequence has **no holes by construction**, not by retry logic.
The `UPDATE` takes a row lock on the counter for the remainder of the transaction, which
serialises appends for that tenant. That serialisation is *desirable*: it makes the predecessor
lookup deterministic, so two concurrent appends cannot both read the same `prev_hash` and fork the
chain.

- **Predecessor lookup:** `SELECT record_hash FROM audit_log WHERE tenant_id = $1 AND seq = $2 - 1`
  (exact `seq` arithmetic — not `ORDER BY created_at DESC`, which is not unique and forks the
  chain under concurrency).
- **Throughput ceiling:** one serialised append per tenant at a time. Measured against real
  audit volume at integration; if a tenant ever exceeds it, the mitigation is batched writes in
  the writer service, never a non-contiguous sequence. A non-contiguous sequence would break the
  gap-free guarantee and is rejected.

### 8.2 The DB-level trigger signal: a sealed export batch

The signal the exporter reacts to is a **sealed batch row**, not a row-level trigger and not a
`NOTIFY`-only mechanism. New pipeline table (no RLS — pipeline table, `tenant_id` present for
pruning and tracing, consistent with `audit_outbox` / `audit_dead_letter`):

```sql
CREATE TABLE audit_export_batch (
  batch_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id      UUID   NOT NULL,
  seq_from       BIGINT NOT NULL,
  seq_to         BIGINT NOT NULL,
  record_count   INTEGER NOT NULL,
  prev_hash      TEXT   NOT NULL,   -- record_hash of seq_from - 1
  chain_head     TEXT   NOT NULL,   -- record_hash of seq_to
  salt_version   SMALLINT NOT NULL,
  sealed_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  exported_at    TIMESTAMPTZ,
  CONSTRAINT audit_export_batch_range_ck
    CHECK (seq_to >= seq_from AND record_count = seq_to - seq_from + 1),
  CONSTRAINT audit_export_batch_seq_from_uq UNIQUE (tenant_id, seq_from)
);
```

**Sealing** is done by a DB-side sealer job (pg_cron, ~30s cadence) that reads the committed
counter value for the tenant and seals the closed range `[last_sealed + 1, next_seq - 1]`. Because
the counter value is only visible after the allocating transaction commits, a sealed range can
never include an in-flight or rolled-back record.

- The `CHECK (record_count = seq_to - seq_from + 1)` makes a **gap structurally impossible** to
  express — a batch that would span a hole cannot be written.
- `UNIQUE (tenant_id, seq_from)` prevents overlapping or duplicated ranges.
- Across all batches of a tenant, the ranges **tile the sequence space exactly**: no overlap, no
  hole, from `seq = 1` to the highest sealed `seq`. That tiling is the "gap-free" guarantee the
  SRE side can rely on when verifying the archive.

**Signal mechanism (both required).** Sealing fires `pg_notify('audit_export_ready', batch_id)`
*inside the sealing transaction*, so a notification is delivered on commit and never for aborted
work. **`pg_notify` is best-effort and is silently lost when no listener is attached at commit
time**, so it may only be a latency optimisation. The exporter's authoritative discovery path is
polling:

```sql
SELECT * FROM audit_export_batch
 WHERE exported_at IS NULL
 ORDER BY sealed_at
 LIMIT <batch size>;
```

### 8.3 Export state, and the retention gate

```sql
CREATE TABLE audit_export_state (
  tenant_id             UUID PRIMARY KEY,
  exported_through_seq  BIGINT NOT NULL,
  last_chain_head       TEXT   NOT NULL,
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

`exported_through_seq` is the resume point after a crash: the exporter continues from
`exported_through_seq + 1`. It also **gates partition drops** — an `audit_log` daily partition may
only be dropped when the export state proves export complete through that partition's maximum
`seq`. Dropping a partition with an unsealed or unexported batch destroys undurable evidence and
is prohibited.

### 8.4 Hash chain handoff to the immutable archive

- **Record hash:** `record_hash = SHA-256( global_salt ‖ prev_hash ‖ canonical_bytes )`.
- **Canonical bytes** must be deterministic and byte-stable across runs, or re-export is not
  byte-identical: length-prefixed field encoding, timestamps as UTC ISO-8601 with microsecond
  precision, `JSONB` canonicalised with **sorted keys**, and `NUMERIC` rendered as text.
- **`global_salt` is a KMS secret owned by the SRE** — never a repository constant, never a
  table column, never an application config file. A constant salt means anyone with DB read
  access can recompute the chain and forge history.
- **The DB computes `record_hash` at insert time**, which keeps the chain authoritative in the
  engine: `UPDATE`/`DELETE` on `audit_log` are revoked from `app` *and* blocked by a
  `BEFORE UPDATE OR DELETE` trigger, so a privileged-but-not-superuser insider cannot rewrite a
  record and its hash independently.
- The salt is injected into the writer session from KMS and cached there; it is never persisted.
- **Salt rotation:** `audit_log.salt_version` records which salt version signed each record.
  Rotation issues a new version (new KMS key version); the chain **continues** across versions
  because `prev_hash` links records regardless of which salt signed them. A verifier selects the
  salt by the record's `salt_version`. Retired salt versions must remain retrievable in KMS for
  as long as any record signed with them is retained.
- **Chain head publication:** each batch carries `chain_head` = `record_hash` of its last record.
  The SRE side publishes these to the write-once location so the chain is externally verifiable.
  Publish **every** batch head — the head of a batch that is later superseded still proves the
  prefix of the chain that was archived.

### 8.5 What the exporter must do — and must not do

- **No RLS bypass, ever.** The exporter is a cross-tenant background worker and must **not** hold
  `BYPASSRLS` or `SUPERUSER`, and must not own the tenant-scoped tables. It iterates tenants from
  the tenant registry and opens **one transaction per tenant**, setting
  `SET LOCAL app.tenant_id = <tenant>` first, exactly as the application does. `audit_log` stays
  RLS-protected; only the pipeline tables (`audit_export_batch`, `audit_export_state`,
  `audit_outbox`, `audit_dead_letter`) are not.
- **Preserve `seq` order** when writing to the object store. Object layout:
  `s3://<bucket>/tenant=<tenant_id>/seq_from=<n>/<batch_id>.jsonl`, one canonical JSON record per
  line, each line carrying `seq`, `prev_hash`, `record_hash`, `salt_version` and the record body.
- **Idempotent re-export:** the same batch re-exported to the same object key produces
  byte-identical content (canonical serialisation), so a retry is safe under S3 versioning.
- **A failure must never become a silent skip.** On a poison record, the exporter writes to
  `audit_dead_letter` and alerts; it does not advance `exported_through_seq` past the failure.
  A hole in the chain is an integrity incident, not a bookkeeping detail.
- **Verify before you trust:** on export, assert `record_count = seq_to - seq_from + 1` and that
  the first record's `prev_hash` equals the previous batch's `chain_head`. A mismatch is a
  finding and must be raised, not worked around.

### 8.6 Open items for the SRE Engineer (agent-3bdca2fd)

| # | Item | Needed for |
|---|------|-----------|
| 1 | Object Lock bucket name, region (ap-southeast-1) and bucket policy | 8.5 exporter target |
| 2 | KMS key + `global_salt` key, with versioning for salt rotation | 8.4 chain signing |
| 3 | Write-once location for batch chain heads | 8.4 external verifiability |
| 4 | Retention `RetainUntilDate` values (Legal Counsel, item 5 in Section 5 — still open) | 8.3 partition-drop gate |
| 5 | Confirmation that retention exceeds the longest filing-backlog re-submission window owned by ACCO-015 | 8.3, AC6 |
| 6 | Exporter runtime shape (job vs. sidecar) and its DB role | 8.5 |

**Answers to the two questions asked of me:**

1. *Which DB-level signal triggers the export writer?* — the **sealed `audit_export_batch` row**,
   discovered by polling `WHERE exported_at IS NULL` (Section 8.2), with
   `pg_notify('audit_export_ready')` as an optional low-latency hint only.
2. *What is the export batch/ordering guarantee?* — **per-tenant, gap-free, contiguous `seq`
   ranges** allocated in the same transaction as the audit insert and tiled exactly across
   batches; the hash chain is one chain per tenant over that sequence space, and a range that
   would span a hole cannot be represented because of the table `CHECK` constraint (Sections
   8.1-8.3).

**Next owner:** SRE Engineer (agent-3bdca2fd) for items 1-6 above; Database Engineer
(agent-dcc4da7f) for the `audit_export_batch` / `audit_export_state` / `audit_seq_counter` DDL
(added to the ACCO-018 Step 1 migration set) and for the exporter's per-tenant read path.
