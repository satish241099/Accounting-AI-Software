# Audit Log Design — ACCO-018
**Author:** Data Engineer (agent-0860c9fb)
**Date:** 2026-10-24
**Status:** Design Proposal v0.1 — pending Data Lead review
**Feature:** F-MVIJZ4YO-002C-17YV → Slice SL-MVIJXKP1-001B-5CRH → Milestone MS-MVIJXDQ3-000Z-8FPD → Mission M-MVIJX5F9-000O-MY23

---

## Design Goals

1. **Immutable evidence-grade records** for every access to Restricted-class data and every filing event.
2. **Tamper-evident** — alteration or deletion is detectable by anyone with chain verification tools.
3. **Tenant-scoped** — audit queries cannot widen scope across clients (enforced at data layer per docs/db-contracts.md Part 2).
4. **Secret-safe** — no tokens, certificates, passwords, or full bank credentials in audit records.
5. **Retention-compliant** — supports WORM/Object Lock and legal-hold for PDPA 2024 / AMLA obligations.
6. **Extensible** — schema can accommodate future AMLA SAR-filing requirements without migration.

---

## §1 — Canonical Event Schema

### 1.1 Core Table: `audit_log`

```sql
CREATE TABLE audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,              -- actor's firm workspace (RLS partition)
    occurred_at     TIMESTAMPTZ NOT NULL,       -- event wall-clock time
    actor_id        UUID NOT NULL,              -- user, service, or system identifier
    actor_type      VARCHAR(20) NOT NULL,       -- 'user' | 'service' | 'system' | 'cron' | 'external'
    action          VARCHAR(40) NOT NULL,       -- see §1.2
    entity_type     VARCHAR(40) NOT NULL,       -- see §1.3
    entity_id       VARCHAR(128) NOT NULL,      -- entity reference (UUID or external ID)
    entity_tenant_id UUID,                      -- client whose data was accessed (may differ from actor's firm)
    request_id      UUID,                       -- correlation ID from originating request
    outcome         VARCHAR(20) NOT NULL,       -- 'success' | 'failure' | 'partial'
    metadata        JSONB,                      -- context: ip, user_agent, source_module, filing details
    before_state    JSONB,                      -- pre-mutation state (non-restricted fields only)
    after_state     JSONB,                      -- post-mutation state (non-restricted fields only)
    chain_hash      BYTEA NOT NULL,             -- SHA-256 tamper chain (see §2)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()  -- write time (may differ from occurred_at for batch)
);
```

**Constraints:**
- `tenant_id` carries the actor's firm workspace — the RLS partition key. Per docs/db-contracts.md Part 2: `current_setting('app.tenant_id', true)::uuid`.
- `entity_tenant_id` is nullable — not all events target a specific client entity (e.g., system config changes).
- `before_state` and `after_state` are redacted at write time — see §4.
- Money values in metadata/before/after use `numeric(19,2)` cast to string, **never float**.

### 1.2 Action Taxonomy

| Category | Actions | Description |
|----------|---------|-------------|
| **Restricted-class access** | `restricted.read`, `restricted.write`, `restricted.delete_attempt` | Access to bank credentials, tax IDs, employee payroll, KYC documents |
| **Filing events** | `filing.submit`, `filing.validate`, `filing.invalidate`, `filing.cancel`, `filing.resubmit` | MyInvois/LHDN filing lifecycle |
| **Filing status** | `filing.status_change` | External status updates (LHDN callback, polling result) |
| **Audit access** | `audit.query`, `audit.export` | Someone reading or exporting the audit log itself |
| **System** | `system.migration`, `system.config_change`, `system.backup` | Infrastructure-level events |
| **Tenant lifecycle** | `tenant.create`, `tenant.delete`, `tenant.onboard`, `tenant.legal_hold_set` | Client workspace management |

### 1.3 Entity Types

```
bank_credential, tax_id, payroll_record, kyc_document, invoice, payment, filing,
filing_submission, filing_document, client_workspace, user_account, api_key,
system_config, audit_record
```

### 1.4 RLS Policies

```sql
-- Audit records are tenant-scoped at the firm workspace level
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log FORCE ROW LEVEL SECURITY;

CREATE POLICY audit_tenant_isolation ON audit_log
  USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);

-- Insert policy: only allow inserts with a valid tenant context
CREATE POLICY audit_insert ON audit_log
  WITH CHECK (
    tenant_id = current_setting('app.tenant_id', true)::uuid
    AND tenant_id IS NOT NULL
  );
```

### 1.5 Indexes

```sql
-- Primary query patterns
CREATE INDEX idx_audit_tenant_entity ON audit_log (tenant_id, entity_type, entity_id, occurred_at DESC);
CREATE INDEX idx_audit_tenant_action ON audit_log (tenant_id, action, occurred_at DESC);
CREATE INDEX idx_audit_tenant_period ON audit_log (tenant_id, occurred_at DESC);

-- Filing-specific queries
CREATE INDEX idx_audit_filing_events ON audit_log (tenant_id, entity_type, entity_id)
  WHERE entity_type = 'filing_submission';

-- Chain verification (sequential scan on chain_hash)
CREATE INDEX idx_audit_chain ON audit_log (created_at);
```

---

## §2 — Tamper-Evidence Mechanism

### 2.1 Hash-Chain Design

Each audit record carries a `chain_hash` that binds it to its predecessor:

```
chain_hash(n) = SHA-256(
    canonical_form(record_n)  ||
    chain_hash(n-1)
)
```

**Canonical form** is a deterministic byte representation of the record (all fields except `chain_hash` and `id`, sorted by field name, JSON-encoded with sorted keys, UTF-8 encoded).

### 2.2 Concurrent Write Handling

Single-table chains break under concurrent inserts. We use **partitioned chains**:

- The chain is partitioned by `(tenant_id, day_partition)`.
- Within a partition, inserts are serialized via a **Postgres advisory lock**:
  ```sql
  SELECT pg_try_advisory_lock(hashtext('audit_chain::' || $1::text || '::' || $2::date::text));
  -- $1 = tenant_id, $2 = date partition
  -- If lock fails, retry with exponential backoff (max 3 retries → dead-letter)
  ```
- The previous hash is fetched via:
  ```sql
  SELECT chain_hash FROM audit_log
  WHERE tenant_id = $1 AND created_at::date = $2
  ORDER BY created_at DESC LIMIT 1;
  ```
- First record in a partition seeds with a **partition root hash** = SHA-256(tenant_id || partition_date || global_salt).

### 2.3 Daily Merkle Anchors

At end of each day, a batch process:
1. Reads all records for `(tenant_id, day)`.
2. Builds a Merkle tree from the chain hashes.
3. Produces a **daily root hash**.
4. Stores the daily root hash in a separate `audit_log_daily_roots` table:
   ```sql
   CREATE TABLE audit_log_daily_roots (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       tenant_id UUID NOT NULL,
       root_date DATE NOT NULL,
       merkle_root BYTEA NOT NULL,
       record_count BIGINT NOT NULL,
       signed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
       signature BYTEA,  -- HSM/Etcd signed (optional, §2.4)
       UNIQUE (tenant_id, root_date)
   );
   ```

### 2.4 External Anchor (Optional — requires SRE)

- Daily root hashes can be anchored to **AWS CloudTrail** (via PutEvent) or an **AWS KMS signed blob** in S3 with Object Lock.
- This provides external, provider-verified tamper evidence beyond the Postgres chain.
- **Routing ask:** SRE Engineer (agent-3bdca2fd) via ACCO-012/ACCO-015 — KMS signing + S3 Object Lock setup.

### 2.5 Chain Verification

Verification tool (for audit/compliance officers):
1. Load all records for a tenant + date range.
2. Re-compute each `chain_hash` from canonical form + previous hash.
3. Compare computed hash to stored `chain_hash`.
4. Any mismatch → tamper detected at that point and all subsequent records.

---

## §3 — Retention Strategy & Legal Basis

### 3.1 Retention Period

| Record Category | Minimum Retention | Legal Basis |
|-----------------|-------------------|-------------|
| Restricted-class access | 7 years | AMLA §46 (anti-money laundering record-keeping) |
| Filing events | 7 years | LHDN e-Invois regulations, tax authority audit window |
| System events | 3 years | Internal operational record-keeping |
| Audit access logs | 7 years | Audit trail integrity (meta-audit) |
| Tenant lifecycle | Duration of tenancy + 7 years | PDPA 2024 §22 (data retention obligations) |

**Legal basis note:** PDPA 2024 permits retention where required by law (AMLA, LHDN). The legal hold mechanism (§3.3) provides the PDPA-compliant override for active investigations.

### 3.2 Storage Architecture

**Hot tier (Postgres, queryable):**
- Current year's audit records, fully indexed.
- Vacuum-safe: `audit_log` is append-only, no DELETE/UPDATE.
- Growth estimate: 50K events/day × 365 days × ~1KB average = ~18 GB/year per firm.

**Warm tier (S3 Parquet, exported weekly):**
- Records older than 90 days are exported to S3 in partitioned Parquet format.
- S3 bucket with **Object Lock in Compliance Mode** — once written, cannot be deleted or overwritten until retention expires.
- Partition: `s3://audit-logs-{env}/{tenant_id}/year={YYYY}/month={MM}/`
- **Routing ask:** SRE Engineer (agent-3bdca2fd) via ACCO-015 — S3 bucket provisioning with Object Lock.

**Cold tier (glacier, 7+ years):**
- Records older than 5 years move to S3 Glacier Deep Archive.
- Object Lock retention extends into Glacier (S3 supports this).

### 3.3 Legal Hold

```sql
CREATE TABLE audit_legal_hold (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    case_id VARCHAR(64) NOT NULL,       -- internal case reference
    reason TEXT NOT NULL,               -- legal basis for hold
    initiated_by UUID NOT NULL,         -- legal counsel or compliance officer
    initiated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    released_at TIMESTAMPTZ,            -- NULL means active
    released_by UUID,
    scope JSONB NOT NULL,              -- filter: { tenant_ids, date_range, entity_types, action_types }
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

- When a legal hold is active, the export/cleanup process must **skip** matching records even if retention period has expired.
- Legal holds are themselves logged to `audit_log` with action `tenant.legal_hold_set`.

### 3.4 Data Residency

- All audit storage (Postgres hot tier, S3 warm/cold tiers) stays in **ap-southeast-1**.
- Cross-border export (e.g., external BI tooling) requires explicit legal review (ACCO-051).
- **No exception** — this is a hard constraint per PDPA 2024.

---

## §4 — Secret Redaction Rules

### 4.1 Fields That MUST NOT Appear in Audit Records

| Category | Examples |
|----------|----------|
| Auth tokens | JWT, bearer tokens, refresh tokens, session cookies |
| Certificates | Digital certificate PEM, private keys, CA bundles |
| Passwords | DB passwords, API keys, encrypted-at-rest keys |
| Bank credentials | Full account numbers, IBANs, routing numbers |
| PII | NRIC/FIN numbers, full addresses, phone numbers |

### 4.2 Redaction Strategy

Redaction happens **at the write path**, not at read time:

```typescript
// Pseudocode: redaction middleware before audit_log insert
function redactForAudit(record: AuditRecord): AuditRecord {
    if (record.entity_type === 'bank_credential') {
        // Store only last-4 of account number
        record.metadata = maskAllButLast4(record.metadata, ['account_number', 'iban']);
    }
    if (record.entity_type === 'filing') {
        // Filing metadata may contain documentHash (OK) but not auth tokens
        delete record.metadata?.authToken;
        delete record.metadata?.certificate;
    }
    // General: strip any field matching secret patterns
    record.metadata = stripSecretPatterns(record.metadata);
    record.before_state = stripSecretPatterns(record.before_state);
    record.after_state = stripSecretPatterns(record.after_state);
    return record;
}
```

### 4.3 Verification

- The `error_message` field is sanitized at write time (no stack traces with secrets).
- The `metadata.ip_address` is stored in full (needed for forensic investigation) but classified Confidential.
- Unit tests must verify redaction for every entity type — see ACCO-018 step 8.

---

## §5 — Audit-of-Audit (Meta-Audit)

### 5.1 Audit Query Logging

Every SELECT/EXPORT against `audit_log` generates a meta-audit record:

```sql
-- Logged automatically by the audit query interceptor
INSERT INTO audit_log (
    tenant_id, occurred_at, actor_id, actor_type,
    action, entity_type, entity_id, metadata, outcome, chain_hash
) VALUES (
    current_setting('app.tenant_id', true)::uuid,
    now(),
    $1, -- querying actor
    $2, -- actor type
    'audit.query',
    'audit_record',
    'self',
    jsonb_build_object(
        'query_tenant_id', $3,   -- tenant scope of the query
        'date_range_start', $4,
        'date_range_end', $5,
        'row_count', $6,
        'export_format', $7
    ),
    'success',
    -- chain_hash computed via write path
    $8
);
```

### 5.2 Scope Guard

- A user cannot query `audit_log` for a `tenant_id` other than their own firm workspace.
- The audit query interceptor enforces this at the application layer.
- The RLS policy on `audit_log` provides database-level enforcement.
- Any attempt to bypass (e.g., direct SQL) fails closed due to `FORCE ROW LEVEL SECURITY`.

---

## §6 — Writer Service Design

### 6.1 Write Path

```
Application/Service
    → AuditLogWriter.log(event)      // synchronous at access point
        → redactForAudit(event)      // secret redaction
        → computeChainHash(event)    // tamper chain
        → INSERT INTO audit_log      // transactional with advisory lock
            → on failure → dead_letter_queue  // retry with exponential backoff
```

- **Synchronous at access point** — restricted-class access logs must be written before the response returns. If the write fails, the access is still denied/allowed but the failure goes to dead-letter + alert.
- **Filing events** can be logged synchronously or asynchronously (filing events have a slower rate). Asynchronous path uses a transaction-outbox pattern to guarantee eventual delivery.

### 6.2 Outbox Pattern (Filing Events)

```sql
CREATE TABLE audit_outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at TIMESTAMPTZ
);
```

A background worker polls `audit_outbox` (ordered by `created_at`) and inserts into `audit_log` with chain hashing.

### 6.3 Dead-Letter Handling

- Failed inserts (advisory lock timeout, DB connection loss) go to `audit_dead_letter` table + SNS alert.
- Dead-letter entries are retried with backoff (max 24 hours).
- Persistent failures escalate to SRE alert (ACCO-012 SLO).

---

## §7 — Explicit Routing Asks

### To SRE Engineer (agent-3bdca2fd) via ACCO-012 / ACCO-015:
1. **S3 bucket** with Object Lock in Compliance Mode for audit log exports (warm/cold tier).
2. **KMS key** for signing daily Merkle root hashes (§2.4).
3. **CloudTrail custom event** integration for external anchor (optional, §2.4).
4. **Alert policy**: audit log writer failure rate > 0.1% triggers P1 alert.

### To Legal Counsel (agent-e3d013c7) via ACCO-051:
1. Confirm **retention periods** (§3.1) against PDPA 2024 and AMLA requirements.
2. Define **legal hold process** (§3.3) — who can initiate, approval chain, documentation requirements.
3. Review **data residency** guarantee (§3.4) — any exceptions for external audit/forensic access?

### To Database Engineer (agent-dcc4da7f) via ACCO-007:
1. Migrations for `audit_log`, `audit_log_daily_roots`, `audit_legal_hold`, `audit_outbox`, `audit_dead_letter`.
2. RLS policies + indexes as specified in §1.4 / §1.5.
3. Confirm advisory lock strategy for concurrent chain writes (§2.2).

### To Security Engineer (agent-7a6c2c23):
1. Review redaction rules (§4) for completeness.
2. Approve classification level (Confidential) for audit records.

---

## §8 — Critical Path Note

ACCO-018 depends on ACCO-016 and ACCO-017. ACCO-016 depends on ACCO-007, which depends on ACCO-004. This creates a **6-task serial chain** before any filing core work can ship:

```
ACCO-004 → ACCO-007 → ACCO-016 → ACCO-018 → ACCO-019 → ACCO-014 → ACCO-054
```

**This design doc unblocks:** schema design (step 1), retention/legal basis (step 7), and specialist routing. Implementation can proceed in parallel with ACCO-016/ACCO-017 once they clear — the schema is ready to implement.

**Recommendation:** Consider whether ACCO-018's dependency on ACCO-016 is a hard requirement for schema creation (it is not — schema exists before isolation harness runs). The real dependency is ACCO-007 (Postgres exists) for migration, and ACCO-017 (filing events) for the filing event hooks. The tenant isolation harness (ACCO-016) is a test/validation concern, not a schema concern.

---

## Appendix A — Entity Type → Restricted Class Matrix

| Entity Type | Restricted? | Logging Requirement |
|-------------|-------------|---------------------|
| bank_credential | Yes (Restricted-class) | Every read/write at access point |
| tax_id | Yes (Restricted-class) | Every read/write at access point |
| payroll_record | Yes (Restricted-class) | Every read/write at access point |
| kyc_document | Yes (Restricted-class) | Every read/write at access point |
| invoice | No (Standard) | Only on mutation |
| payment | No (Standard) | Only on mutation |
| filing | Yes (Confidential) | Every submission/validation/invalidation/cancellation |
| filing_submission | Yes (Confidential) | Every status change |
| api_key | Yes (Restricted-class) | Every read/use/rotation |
