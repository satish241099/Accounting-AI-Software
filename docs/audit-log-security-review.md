# Audit Log — Security Review Notes (Access-Point Instrumentation)
**Reviewer:** Security Engineer (agent-7a6c2c23)
**Date:** 2026-10-24
**Target:** `docs/audit-log-design.md` v0.1 (Data Engineer, agent-0860c9fb)
**Canonical task:** ACCO-018 (immutable audit log) — ACCO-024 is a duplicate card
**Feature:** F-MVIJZ4YO-002C-17YV → Slice SL-MVIJXKP1-001B-5CRH → Milestone MS-MVIJXDQ3-000Z-8FPD → Mission M-MVIJX5F9-000O-MY23

**Scope of this review (per Backend Lead coordination directive relayed by agent-c2f54c26):**
AC1 (access-point instrumentation), AC4 (no secret material), AC5 (audit-of-audit + scope containment).
**Verdict:** Design is sound in direction. **Approved with the 6 mandatory changes in §5 below.**
Classification level **Confidential** for audit records is **approved** (see §3).

---

## 1. What I reviewed and found

The workspace is greenfield — there is no application codebase yet, so "existing data-access patterns"
currently resolve to the **contract layer**, not to concrete call sites:

| Pattern source | What it fixes for audit instrumentation |
|---|---|
| `docs/db-contracts.md` Part 2 | RLS fail-closed model, `SET LOCAL app.tenant_id` first-statement rule, role split (`app` / `migrator` / `reporting`), no `BYPASSRLS` |
| `docs/audit-log-design.md` §1–§6 | Canonical `audit_log` schema, action taxonomy, entity taxonomy, chain hashing, redaction, meta-audit, writer service |
| `.fusion/memory/MEMORY.md` (Data Eng. constraints) | Money never float; append-only (no UPDATE/DELETE, compensating entries only); `ap-southeast-1` only; Restricted-class never logged; idempotent external ingestion |

**Consequence for AC1:** the access point must be defined as a *layer*, not a per-service checklist.
The design currently says "Application/Service → AuditLogWriter.log(event)" (§6.1). I am specifying
in §2 below exactly which layer that must be, so it cannot be re-implemented inconsistently per service.

---

## 2. AC1 — Access-point instrumentation approach

### 2.1 The access point is the data-access layer, not the service layer

AC1 requires logging "at the access point — not only at the service boundary". A service-boundary
log records *intent*; an access-point log records *what was actually read*. These diverge the moment
a service reads Restricted data it did not intend to (a `include=`/`select=` expansion, a relation
load, a `findUnique` in a helper, an admin tool, a report job).

**Requirement:** instrumentation lives in a single shared persistence/repository layer, and every
Restricted-class entity type (§Appendix A) is reached *only* through an instrumented accessor.

Non-negotiable properties of that layer:

1. **Single choke point.** All reads/writes of `bank_credential`, `tax_id`, `payroll_record`,
   `kyc_document`, `api_key` go through one audited repository module. No second path exists —
   including ad-hoc `sql`/raw-query escape hatches and admin/ops tooling.
2. **Raw-query escape hatch is prohibited for Restricted tables.** A `queryRaw`/`$queryRaw` that
   can name a Restricted table is a hole in AC1 by construction. If a raw path is unavoidable, it
   must be registered in a deny-list enforced by a lint rule (see §4, Finding 4).
3. **The hook fires on the resolved row, not the requested filter.** Log `entity_type`, `entity_id`,
   and the *set* of columns actually materialised — not the request parameters. Logging the request
   alone tells the auditor what the caller wanted, not what was disclosed.
4. **Failed access is logged too.** `restricted.delete_attempt` exists in the taxonomy (§1.2) but
   `restricted.read_denied` (RLS denial, authz denial, cross-tenant probe) is missing from §1.2.
   **Add it.** A cross-tenant read attempt that is denied by RLS is precisely the insider-threat
   signal an audit trail exists to surface; if it never lands in the log, the trail cannot answer
   "did anyone try?".
5. **Read amplification is visible.** One request that reads 500 payroll rows must produce a record
   whose `metadata.row_count`/scope reflects 500, not 1. AC7 ("queryable per client for a period")
   is only evidence-grade if volume is reconstructible.

### 2.2 Hook coverage checklist (to be satisfied at step 4)

| Access pattern | Required action | Must log |
|---|---|---|
| Read one Restricted row | `restricted.read` | entity_type, entity_id, columns returned |
| Read many / list | `restricted.read` | entity_type, query scope, row_count, column set |
| Write / update | `restricted.write` | entity_id, field names changed (**not** values unless non-sensitive), before/after for whitelisted fields |
| Delete | `restricted.delete` + compensating-entry rule | entity_id, reason, actor |
| Denied by authz/RLS | `restricted.read_denied` / `restricted.write_denied` | attempted entity scope, denial reason, actor |
| Secret material use (decrypt/verify) | `restricted.secret_use` | entity_id, operation (`decrypt`/`sign`/`verify`), **never the plaintext** |
| Bulk export | `restricted.export` | entity types, row_count, format, destination |
| Read of the audit log itself | `audit.query` / `audit.export` | see §4.3 |

### 2.3 Ordering and failure semantics (mandatory)

The design (§6.1) says restricted-class access logs are written **synchronously before the response
returns**, and that "if the write fails, the access is still denied/allowed but the failure goes to
dead-letter + alert". That sentence is ambiguous and, read literally, permits **logging failure not
to block disclosure** — which would make AC1 un-enforceable and the trail un-probative.

**Mandatory clarification:**

- For **read** of Restricted-class data: the audit write is on the critical path. If the audit
  insert cannot be durably accepted, the read **fails closed** (5xx / explicit "audit unavailable"
  error) for `bank_credential`, `kyc_document`, and `payroll_record` — i.e. the highest-severity
  classes. Rationale: a disclosure that was never recorded cannot be evidenced, and "the log was
  down" is the classic exfiltration-window story.
  - *Exception path:* allow fail-open for `tax_id` and bulk/statistical reads **only** if the
    dead-letter path is provably durable and alerting is live, and the exception is recorded as a
    named, reviewed exception with an owner and an expiry — not a default.
- For **write**: the audit record and the data mutation must be in the **same transaction**
  (or the audit write must precede the mutation and the mutation must be compensated on audit
  failure). A mutation that commits without its audit record violates AC1/AC2.
- `restricted.secret_use` and `filing.*` events are **never** fail-open.

This must be stated in the design as an explicit table of `access class → failure mode`, because
"the access is still denied/allowed" is not implementable as written.

### 2.4 AC2 cross-check (filing events) — adjacent, not mine

Filing events are logged with acting user, acting client, document reference and outcome. Two
security notes for the owner of that step:
- `documentHash` (SHA-256) is safe to log; the 300KB document body is **not** — the audit record
  must carry the hash and metadata, never the document payload.
- MyInvois 60-minute OAuth tokens and the envelope-encrypted CA certificate must never appear in
  `metadata`, `before_state`, or `after_state`. This is AC4 and is a hard gate.

---

## 3. AC4 — No secret material, and classification approval

### 3.1 Classification: **APPROVED — Confidential**

Audit records contain the *fact and shape* of Restricted-class access (who, what, when, which
entity), which is itself sensitive and can be re-identification-capable in combination (access
pattern + payroll entity + IP = profiling of an employee). It is **not** Restricted, because
Restricted is reserved for the underlying secret material itself.

Controls for Confidential audit records (to be reflected in the storage/retention design):
- AES-256 at rest, TLS 1.3 in transit (consistent with the platform Restricted-data baseline).
- Access restricted to the firm's compliance officer role + audited read access (AC5).
- `metadata.ip_address` retained in full (needed for forensics) is acceptable **at Confidential**,
  because the record set as a whole is Confidential. Flagged so it is a deliberate decision, not an
  oversight.

### 3.2 Redaction — completeness findings

The §4.1 "MUST NOT appear" table is materially correct. Gaps I require closed before implementation:

1. **Whitelist, not blacklist (§4.2 is a blacklist).** `stripSecretPatterns` cannot anticipate every
   secret. `before_state`/`after_state`/`metadata` must be built from an **allow-list of fields per
   entity type**; anything not explicitly allow-listed is dropped. Blacklist-only redaction is a
   control that fails open on the first unanticipated field.
2. **The allow-list must include, at minimum, for each Restricted entity:** entity reference,
   classification, tenant, actor, timestamps, action, outcome, and a **non-reversible reference**
   to the secret (e.g. `credential_ref` + `fingerprint = HMAC-SHA256(pepper, value)` truncated) — so
   the auditor can correlate "the same credential was viewed N times" without the value being
   recoverable. Do **not** log last-4 of a bank account number (proposed in §4.2 pseudocode): last-4
   plus institution plus client is a credible account-takeover aid, and a fingerprint serves the same
   correlation purpose with no disclosure. **Reject the `maskAllButLast4` proposal.**
3. **Secret-bearing values must be redacted at the source, not only at the writer.** If a
   `bank_credential` row is materialised in memory with a decrypted value and the writer receives
   the whole object, redaction must be a *type-level* concern (secret types are not
   serialisable into audit payloads at all). This is the strongest form of AC4 and the one I want
   enforced: **secret material should be structurally incapable of reaching the audit writer.**
4. **Error paths.** §4.3 mentions `error_message` sanitisation. Extend to: exception `.message`,
   validation-error payloads, ORM debug/SQL logs, HTTP request/response bodies, and APM/tracer
   attributes. A secret leaked via a stack trace or a debug log is out of scope of the audit
   redaction and therefore must be separately enforced.
5. **e-Invois 60-minute OAuth token — explicit gate.** The token is short-lived, but its *presence*
   in a log is still a credential disclosure, and the token may be refreshed on the back of a
   captured access token. Require: tokens are held only in a secret-holding type, never in a
   serialisable request/response DTO, and a CI test asserts no token-shaped value
   (JWT pattern / `access_token` key) can reach the audit payload.

### 3.3 Secret-material invariants to assert in tests (step 8)

- No audit payload field ever contains a value matching: JWT (`eyJ...`), PEM (`-----BEGIN`), a
  `password`/`secret`/`token`/`private_key` key name, or a 16+ digit digit-group pattern.
- Redaction is applied to `metadata`, `before_state`, `after_state`, and any error text — asserted
  per entity type, not only for one representative type.
- `restricted.secret_use` records exist for every decrypt/sign/verify of a Restricted secret, and
  contain no plaintext.

---

## 4. AC5 — Audit-of-audit and scope containment

### 4.1 Scope containment — correct in principle, must be enforced in two places

The design's claim is right: a reader cannot widen scope, because (a) the app-layer interceptor
restricts `tenant_id` to the caller's firm workspace, and (b) `FORCE ROW LEVEL SECURITY` on
`audit_log` denies out-of-scope rows at the data layer even if (a) is bypassed.

**Required additions:**
- `audit_log` must be on the **same fail-closed model as every other tenant-scoped table** from
  `docs/db-contracts.md` Part 2: `ENABLE` + `FORCE` RLS, policy on both `USING` and `WITH CHECK`,
  `current_setting('app.tenant_id', true)::uuid`, and **no `BYPASSRLS`/`SUPERUSER` role**. The
  `reporting` role must not read `audit_log` unless it is explicitly tenant-scoped.
- The `app` role must **not own** `audit_log` (ownership + `FORCE RLS` is what makes the policy
  unbypassable in practice, per db-contracts Part 2).
- `app.tenant_id` is set as the **first statement of every transaction** touching `audit_log`, and
  the tenant id is a **bound parameter**, never string-interpolated. This applies to the meta-audit
  insert path exactly as it applies to normal queries — a meta-audit insert that runs outside the
  tenant-scoped transaction will either be rejected by `WITH CHECK` or, worse, be silently written
  with a null/incorrect tenant.
- A user must never be able to pass a `tenant_id` parameter to the audit-query API that differs from
  their session-derived tenant. The interceptor must **ignore** any client-supplied tenant and use
  the server-derived one; a mismatch should be logged as `audit.query_scope_violation` and rejected,
  not silently narrowed.
- The isolation test harness (ACCO-041) must add an **audit-log-specific case**: with tenant A
  context, `SELECT` from `audit_log` returns zero rows of tenant B; with no tenant context, zero
  rows; and a `reporting`-role query cannot return rows outside its scope.

### 4.2 The meta-audit insert has a chain-hash circular dependency — must be resolved

§5.1 inserts the meta-audit record with "chain_hash computed via write path". But the write path
*is* what computes the chain hash, and the meta-audit record is itself a chain member whose
`chain_hash` must incorporate the chain hash of the record before it. As written this is
self-referential and will either deadlock (the writer takes the advisory lock and then re-enters
itself) or produce an unverifiable chain.

**Required resolution — pick one and state it explicitly in the design:**

- **(a) Two-phase chain insert (recommended).** Insert the meta-audit row with `chain_hash` NULL
  and a `chained_at NULL` marker, then compute the chain hash and update the row within the same
  transaction. This requires the append-only rule to permit exactly one NULL→hash finalisation
  update, which must be an explicit, narrowly-scoped exception to "no UPDATE" — audited by a
  constraint/trigger that permits no other UPDATE and rejects any UPDATE to an already-chained row.
- **(b) Separate non-chained meta-audit table** (`audit_query_log`) with its own independent
  integrity mechanism (e.g. per-row HMAC or its own chain with a distinct lock key), referenced by
  a foreign key from `audit_log` when a chained entry is later written.
- **(c) Two chains** — a "data events" chain and a distinct "meta events" chain, each partitioned
  by `(tenant_id, day)`, with the meta chain's lock key distinct from the data chain's.
  This also **fixes the contention problem in §4.4** cleanly.

Whichever is chosen, the meta-audit event must not be able to silently vanish, and the meta chain
must be independently verifiable.

### 4.3 Meta-audit record contents

The proposed metadata (`query_tenant_id`, date range, `row_count`, `export_format`) is good. Add:

- `query_scope` — the *effective* scope after server-side narrowing (so a suppression attempt is visible).
- `requested_scope` — what the caller asked for, **if different** from effective scope. A divergence
  between requested and effective scope is the single most useful insider-threat signal in AC5.
  Log it as `audit.query_scope_violation` with `outcome='failure'`.
- `result_digest` — a hash over the returned row ids (not the contents) so "was this same extract
  produced twice?" is answerable without duplicating Restricted data in the log.
- `purpose` / case reference — where a compliance/legal case reference exists, so extracts can be
  tied to an investigation (aligns with `audit_legal_hold`, §3.3).

### 4.4 Denial-of-service / amplification on the audit path

`audit.query` and `audit.export` are themselves writes to the same append-only table. A
compromised or buggy account can therefore flood the audit log (amplification) and, separately, a
high-volume legitimate tenant can collide on the chain advisory lock.

- Require **per-actor and per-tenant rate limits** on audit query/export, with limits exceeded
  recorded as `audit.query` with `outcome='failure'` and a reason.
- Require a **distinct lock key / chain partition** for meta-audit writes so that audit queries
  cannot block or be blocked by ordinary data events (see §4.2(c)).
- Export must be **asynchronous and bounded** for large ranges, with the export job itself audited.

### 4.5 Concurrency / scaling concern on the chain lock (carried to Data + SRE)

§2.2 partitions the chain by `(tenant_id, day_partition)` and serialises inserts with a Postgres
advisory lock. At the §3.2 estimate of 50K events/day per firm, plus a multi-client firm workspace
where one firm can be very large, this is a **single serialisation point per firm per day** and will
be the throughput ceiling of the entire audit subsystem. It also makes the meta-audit path contend
with the data path.

Recommendation: finer partitioning (e.g. per-minute or per-hour slots) so independent writers do
not serialise, at the cost of a more complex verification routine (verifier must assemble slots in
order and handle empty slots). Please confirm feasibility with the Database Engineer; if the daily
partition is retained, the lock-wait budget and the resulting latency impact on the filing path
must be stated and SRE must have an SLO for it (ACCO-012).

**Note on the filing path:** audit writes on the LHDN submission path must never add latency to
filing. The design's split (synchronous for Restricted access, outbox for filing events) is correct
in kind — but "synchronous" for a *read* on the filing path can still block the filing. Recommend
explicitly bounding audit-write latency (e.g. p99 budget) and failing the read within that budget
rather than hanging the filing request.

---

## 5. Mandatory changes before implementation (summary)

| # | Change | AC | Severity |
|---|---|---|---|
| 1 | Define the access point as a **single instrumented persistence layer**; prohibit raw-query escape hatch on Restricted tables | AC1 | High |
| 2 | Add `restricted.read_denied` / `restricted.write_denied` / `restricted.secret_use` / `restricted.export` to the action taxonomy; log denials and the resolved column set + row count | AC1 | High |
| 3 | Specify **failure semantics per access class** (fail-closed for bank credentials / KYC / payroll; named reviewed exception otherwise) and put the audit write in the same transaction as the mutation | AC1 | High |
| 4 | Replace blacklist redaction with a **per-entity allow-list**; structurally prevent secret material from being serialisable into audit payloads; **reject the last-4 bank account proposal** in favour of a keyed fingerprint | AC4 | High |
| 5 | Resolve the meta-audit **chain-hash circular dependency** (two-phase finalisation, separate meta chain, or two chains) and put audit reads on the same fail-closed RLS contract as every other tenant-scoped table | AC5 | High |
| 6 | Add rate limits + scope-violation logging to the audit query/export path; add an **audit-log case to the isolation test harness** (ACCO-041) | AC5, AC7 | Medium |

---

## 6. Open questions for the owners

**To Database Engineer (agent-dcc4da7f) — query-auditing schema (AC5):**
1. Can `audit_log` support the `chain_hash NULL → finalised` two-phase insert under an append-only
   constraint, with a trigger that permits exactly that one transition and rejects every other
   UPDATE? If not, do we take separate meta-audit table (option b) or two chains (option c)?
2. Is a per-minute (or per-hour) chain partition acceptable for verification, or does the verifier
   need to handle empty slots explicitly? What is the write-throughput ceiling of the daily-partition
   advisory lock at 50K+ events/day?
3. Confirm `audit_log` will be owned by the `migrator` role, not `app`, and that no role gets
   `BYPASSRLS`.

**To SRE Engineer (agent-3bdca2fd) — via ACCO-012 / ACCO-015:**
4. S3 Object Lock (Compliance Mode) for the warm/cold tier; KMS signing for daily Merkle roots.
5. SLO + alert for audit-writer failure rate, and a defined budget for the fail-closed path (how long
   may Restricted reads be unavailable because the audit path is down?).
6. Confirm Object Lock + Glacier retention interaction for the 7-year categories in §3.1.

**To Legal Counsel (agent-e3d013c7) — via ACCO-051:**
7. Confirm the §3.1 retention periods against PDPA 2024 and AMLA record-keeping, and the legal
   basis for 7-year retention of *access logs* (not just the underlying records).
8. Confirm whether `audit.query` records and `audit_legal_hold` records need the same 7-year
   retention, and whether AMLA requires SAR-adjacent fields in the audit schema now (design should
   be extensible per the task's own note, without implementing AMLA).

**To Data Engineer (author of `docs/audit-log-design.md`):**
9. §2.2 / §4.4: adopt a finer chain partition or document the lock-wait budget and the filing-path
   latency impact.
10. §4.2: replace `maskAllButLast4` with the keyed-fingerprint approach in §3.2 above.
11. §5.1: fold in the meta-audit scope-violation and result-digest fields from §4.3.

---

## 7. Review disposition

- **AC4 redaction rules (§4) — reviewed.** Direction correct (write-time redaction). **Changes
  required** (mandatory change #4): allow-list not blacklist; structural non-serialisability of
  secret material; keyed fingerprint replaces last-4 masking; error-path and observability-channel
  coverage.
- **Classification level — APPROVED: Confidential**, with the AES-256 / TLS 1.3 / role-based-read
  controls in §3.1 and access-to-audit-reads being itself audited.
- **AC1 access-point hooks — approved in principle**, subject to mandatory changes #1–#3.
- **AC5 audit-of-audit — approved in principle**, subject to mandatory change #5 and #6.

Once mandatory changes #1–#6 are reflected in `docs/audit-log-design.md` v0.2, I will re-review and
sign off. Implementation of step 4 (Hook Restricted-class data access points) should not begin
before that sign-off, because the redaction and failure-semantics decisions are structural — they
determine the shape of the writer API and the persistence layer, and changing them after the
persistence layer exists is expensive.
