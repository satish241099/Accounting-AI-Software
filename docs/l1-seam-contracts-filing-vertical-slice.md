# L1 Seam Contracts — Filing Vertical Slice (Doc Type 01)

**Version:** v1.0 (frozen) · **Date:** 26 Oct 2026 · **Author:** Legacy Modernization Specialist (agent-9fde6dbd)
**Status:** **FROZEN — Architecture Lead sign-off received 26 Oct 2026 (msg-a7626cc8); L1 freeze complete**
**Basis:** `docs/legacy-modernization-strategy.md` v0.2 · `docs/legacy-facade-contracts.md` v0.1 (FROZEN, Architecture Lead sign-off 26 Oct 2026, msg-c0a1c517) · `docs/db-contracts.md`
**Lineage:** M-MVN9TORT-000D-W0X7 → SL-MVNRWZPU-0005-2118 → F-MVNRX1RS-0006-XEXC (Feature: L1 Seam Contracts — Filing Vertical Slice)

---

## 0. Purpose and Scope

This document is the **L1 deliverable** for the filing vertical slice: the concrete seam contract between the **e-Invoice Orchestration** domain module and the **FilingGateway.v1** implementation seam for document type 01 (standard e-Invoice).

**In scope:**
- FilingGateway.v1 implementation seam (operations, command envelope, canonical types, idempotency namespace)
- e-Invoice Orchestration seam (inputs/outputs using canonical types only)
- Boundary between them (data flow, `document_hash` ownership, token lifecycle encapsulation, 300KB limit)
- Traceability to frozen L0 canonical types and §7 dependency direction
- Extended error taxonomy, idempotency semantics, and audit hooks for L1

**Out of scope:**
- Any implementation code or adapter logic
- Doc types other than 01 (02, 03, 04, 11–14 are future slices)
- TaxFilingGateway, PayrollGateway, CompanyRegistryGateway, LegacySuiteAdapter
- MyInvois SDK internals or token refresh logic (remains inside FilingGateway adapter per INV-5)

**Language neutrality:** Same convention as L0 — pseudo-TypeScript shapes, field names/nullability/enums/error codes normative across runtimes. Architecture Lead owns binding decision per runtime.

---

## 1. L0 Canonical Types and Invariants — Reconciled Baseline

The following L0 types and invariants are **frozen** and inherited verbatim. No new canonical types are introduced at L1.

### 1.1 Canonical Types (from L0 §2)

| Type | Reference |
|---|---|
| `TenantContext` | L0 §2.1 |
| `ActorRef` | L0 §2.1 |
| `CorrelationRef` | L0 §2.1 |
| `ConfidenceLabel` (VERIFIED \| DERIVED \| INFERRED \| UNKNOWN) | L0 §2.1 — schema-enforced per INV-7 |
| `AuditOutcome` (SUCCESS \| PARTIAL \| REJECTED_EXTERNALLY \| FAILED_LOCAL \| TIMEOUT_UNRESOLVED) | L0 §2.1 |
| `CanonicalField<T>` | L0 §2.2 |
| `Money` (decimal string, currency: "MYR") | L0 §2.2 |
| `Quantity` (decimal string, unit) | L0 §2.2 |
| `TaxPoint` | L0 §2.2 |
| `PartyRef` | L0 §2.2 |
| `DocumentRef` | L0 §2.2 |
| `ComplianceWorkItem` | L0 §2.3 |
| `AuditRecord` | L0 §2.4 |
| `CanonicalInvoiceDocument` | L0 §3.1 |
| `FilingSubmissionResult` | L0 §3.1 |
| `FilingStatusResult` | L0 §3.1 |

### 1.2 L0 Invariants (from L0 §1 — all apply)

| # | Invariant | L1 Impact |
|---|---|---|
| INV-1 | Tenant context travels in the command, never as ambient state | Orchestration must pass `tenant` in every command; FilingGateway verifies |
| INV-2 | Idempotency key required on every write, namespaced per gateway | Orchestration generates `filing:<client_entity_id>:<key>`; FilingGateway validates namespace |
| INV-3 | Canonical domain types only cross boundary | Orchestration produces `CanonicalInvoiceDocument`; FilingGateway returns `FilingSubmissionResult`/`FilingStatusResult` |
| INV-4 | Every gateway call audit-logged | L1 extends `interface_ref` values to `FilingGateway.v1.submit`, `FilingGateway.v1.status`, `FilingGateway.v1.reconcileAfterTimeout` |
| INV-5 | Credential/token material never surfaces upward | FilingGateway encapsulates 60-min token lifecycle; no token in command/result/error |
| INV-6 | Facade seams defined by external system capability | FilingGateway seam = MyInvois SDK capabilities for doc type 01 |
| INV-7 | Unknown is first-class; confidence label schema-enforced | All canonical fields carry `ConfidenceLabel`; UNKNOWN never dropped |
| INV-8 | Timeouts are reconcile-only, never blind resubmit | Orchestration on `E_EXTERNAL_TIMEOUT` calls `reconcileAfterTimeout` only |
| INV-9 | Idempotency keys namespaced per gateway, never shared | `filing:` namespace exclusive to FilingGateway |
| INV-10 | Fail closed on unresolved tenant context | FilingGateway rejects command if `tenant_id` cannot be verified |

### 1.3 L0 Error Taxonomy Baseline (from L0 §5)

| Code | Meaning | Retriable |
|---|---|---|
| `E_UNAUTHORIZED` | Token invalid/expired and refresh failed | No |
| `E_EXTERNAL_TIMEOUT` | External call timed out | **Reconcile only** (INV-8) |
| `E_EXTERNAL_ERROR` | External system returned error | Case-by-case |
| `E_VALIDATION` | Command failed canonical validation | No |
| `E_HASH_MISMATCH` | `document_hash` verification failed | No |
| `E_DOCUMENT_TOO_LARGE` | Document exceeds 300KB limit | No |
| `E_IDEMPOTENCY_CONFLICT` | Idempotency key seen with different payload | No |
| `E_TENANT_CONTEXT_MISSING` | Tenant context absent/invalid | No (fail closed) |
| `E_ADAPTER_INTERNAL` | Adapter bug / invariant violation | No |

---

## 2. FilingGateway.v1 Implementation Seam (L1)

### 2.1 Operations (Exactly Three — Frozen from L0 §3.1)

```
submit(command: SubmitFilingCommand)         -> FilingSubmissionResult
status(command: FilingStatusQuery)           -> FilingStatusResult
reconcileAfterTimeout(command: ReconcileCommand) -> FilingStatusResult
```

### 2.2 Command Envelope (L1 Extension — Normative)

```
Command — {
  tenant:        TenantContext,           // INV-1: travels in command
  actor:         ActorRef,                // INV-4: audit attribution
  correlation:   CorrelationRef,          // INV-4: traceability
  idempotency_key: string,                // INV-2, INV-9: namespaced "filing:<client_entity_id>:<key>"
  requested_at:  timestamp                // ISO 8601, UTC
}
```

**Normative rules:**
- `idempotency_key` **MUST** match pattern `^filing:[0-9a-f-]{36}:.{1,128}$` (client_entity_id UUID + caller-chosen suffix ≤ 128 chars)
- FilingGateway **rejects** keys not matching namespace with `E_VALIDATION`
- `tenant.client_entity_id` **MUST** match the UUID in the idempotency key namespace; mismatch → `E_TENANT_CONTEXT_MISSING`

### 2.3 Operation Signatures (L1 — Normative Shapes)

#### `submit`

```
SubmitFilingCommand — {
  command:       Command,
  document:      CanonicalInvoiceDocument,   // L0 canonical type, doc_type MUST be "01"
  document_hash: string                      // SHA-256 hex, computed once at creation (L0 §3.1 rule 2)
}

FilingSubmissionResult — {
  document_id:      UUID,                    // Internal document ID
  submission_ref:   string | null,           // MyInvois submissionUid (if accepted)
  status:           SUBMITTED | VALID | INVALID | CANCELLED | ACCEPTED | REJECTED,
  accepted_at:      timestamp | null,
  rejection_reason: string | null            // Canonical, not vendor code
}
```

**L1-specific normative rules:**
1. `document.doc_type` **MUST** be `"01"`; other values → `E_VALIDATION`
2. `document_hash` is **verified** (recomputed and compared) by FilingGateway; mismatch → `E_HASH_MISMATCH` (L0 §3.1 rule 2)
3. Document size **MUST NOT** exceed 300KB (serialized canonical JSON); exceedance → `E_DOCUMENT_TOO_LARGE` (L0 §3.1 rule 3)
4. On timeout: returns `E_EXTERNAL_TIMEOUT`; caller **MUST** call `reconcileAfterTimeout` — `submit` never retried (INV-8)
5. Duplicate detection: if idempotency key seen with identical `document_hash` → returns existing `FilingSubmissionResult` (idempotent success); if different `document_hash` → `E_IDEMPOTENCY_CONFLICT`

#### `status`

```
FilingStatusQuery — {
  command:     Command,
  document_id: UUID
}

FilingStatusResult — {
  document_id:  UUID,
  status:       SUBMITTED | VALID | INVALID | CANCELLED | ACCEPTED | REJECTED,
  external_ref: string | null,               // MyInvois submissionUid or cancellationUid
  as_of:        timestamp,
  confidence:   ConfidenceLabel              // L0 schema-enforced (INV-7)
}
```

#### `reconcileAfterTimeout`

```
ReconcileCommand — {
  command:     Command,
  document_id: UUID
}

FilingStatusResult — (same as status)
```

**L1-specific normative rules:**
1. **Read-only with respect to external system** — queries MyInvois status, does not re-submit (L0 §3.1 rule 6)
2. Called **only** after `submit` returned `E_EXTERNAL_TIMEOUT` (INV-8)
3. Idempotency key **MUST** match the original `submit` command's key; mismatch → `E_VALIDATION`

---

## 3. e-Invoice Orchestration Seam (L1)

### 3.1 Responsibility Boundary

| Concern | Owner |
|---|---|
| Document assembly from ledger/draft | e-Invoice Orchestration |
| `document_hash` computation (once, at creation) | e-Invoice Orchestration (document model) |
| `ConfidenceLabel` assignment per field | e-Invoice Orchestration |
| Idempotency key generation (namespaced) | e-Invoice Orchestration |
| Command envelope construction (tenant/actor/correlation) | e-Invoice Orchestration |
| MyInvois token lifecycle | **FilingGateway adapter only** (INV-5) |
| 300KB enforcement with user-facing error | FilingGateway adapter |
| Duplicate detection / cancellation rules | FilingGateway adapter |
| External call, timeout, reconcile | FilingGateway adapter |

### 3.2 Orchestration Inputs (Canonical Types Only)

```
OrchestrationInput — {
  tenant:           TenantContext,
  actor:            ActorRef,
  correlation:      CorrelationRef,
  invoice_draft:    InvoiceDraft,              // Internal draft model (not canonical)
  client_entity_id: UUID                       // For idempotency namespace
}
```

### 3.3 Orchestration Outputs (Canonical Types Only)

```
OrchestrationOutput — {
  document:         CanonicalInvoiceDocument,  // doc_type = "01", hash computed, confidence labelled
  command:          Command,                   // Envelope with idempotency_key = "filing:<client_entity_id>:<key>"
  submission_result: FilingSubmissionResult | null,  // Null if submit not yet called
  status_result:    FilingStatusResult | null
}
```

### 3.4 Orchestration Flow (Normative)

```
1. Assemble CanonicalInvoiceDocument from invoice_draft
   - Map every field → CanonicalField<T> with ConfidenceLabel
   - Compute document_hash = SHA-256(canonical_json) once
   - Set document.confidence = aggregate of field confidences

2. Generate idempotency_key = "filing:" + client_entity_id + ":" + crypto.randomUUID()

3. Construct Command envelope with tenant, actor, correlation, idempotency_key, requested_at

4. Call FilingGateway.v1.submit(SubmitFilingCommand)

5. On SUCCESS (FilingSubmissionResult):
   - Persist document_id, submission_ref, status
   - Return OrchestrationOutput

6. On E_EXTERNAL_TIMEOUT:
   - Persist document_id, idempotency_key, correlation
   - Call FilingGateway.v1.reconcileAfterTimeout(ReconcileCommand) with SAME idempotency_key
   - On reconcile result: persist final status, return OrchestrationOutput

7. On other errors (E_HASH_MISMATCH, E_DOCUMENT_TOO_LARGE, E_VALIDATION, E_IDEMPOTENCY_CONFLICT, E_TENANT_CONTEXT_MISSING):
   - Do NOT retry submit
   - Return error to caller with full AuditRecord context
```

---

## 4. Boundary Between Orchestration and FilingGateway (L1)

### 4.1 Data Flow Diagram

```
e-Invoice Orchestration                    FilingGateway.v1 Adapter
┌─────────────────────────┐                ┌─────────────────────────┐
│ 1. Build Canonical      │                │                         │
│    Invoice Document     │                │                         │
│    - doc_type: "01"     │                │                         │
│    - fields: map<       │                │                         │
│        CanonicalField>  │                │                         │
│    - document_hash      │                │                         │
│    - confidence         │                │                         │
├─────────────────────────┤                │                         │
│ 2. Generate idempotency │                │                         │
│    key: "filing:        │                │                         │
│    <client_entity_id>: │                │                         │
│    <uuid>"              │                │                         │
├─────────────────────────┤                │                         │
│ 3. Build Command        │                │                         │
│    envelope             │                │                         │
│    (tenant, actor,      │                │                         │
│     correlation,        │                │                         │
│     idempotency_key,    │                │                         │
│     requested_at)       │                │                         │
├─────────────────────────┤   SubmitFilingCommand
│ 4. submit(cmd) ─────────▶                │                         │
│                         │                │ 5. Verify document_hash │
│                         │                │    matches recomputation│
│                         │                │    (mismatch →          │
│                         │                │    E_HASH_MISMATCH)     │
│                         │                │ 6. Enforce 300KB limit  │
│                         │                │    (exceed →            │
│                         │                │    E_DOCUMENT_TOO_LARGE)│
│                         │                │ 7. Check idempotency    │
│                         │                │    key namespace +      │
│                         │                │    payload match        │
│                         │                │ 8. Delegate to existing │
│                         │                │    filing service       │
│                         │                │    (ACCO-017/054)       │
│                         │                │    - Token lifecycle    │
│                         │                │      inside adapter     │
│                         │                │    - MyInvois SDK call  │
│                         │                │ 9. On timeout:          │
│                         │                │    return E_EXTERNAL_   │
│                         │                │    TIMEOUT              │
├─────────────────────────┤   FilingSubmissionResult
│ 10. Receive result ◀────│                │                         │
│     or E_EXTERNAL_TIMEOUT│                │                         │
│                         │                │                         │
│ 11a. On SUCCESS:        │                │                         │
│     Persist, return     │                │                         │
│ 11b. On TIMEOUT:        │                │                         │
│     Call reconcile-     │   ReconcileCommand
│     AfterTimeout ──────▶                │ 12. Query MyInvois      │
│                         │                │     status (read-only)  │
│ 13. Receive status ◀────│   FilingStatusResult                   │
└─────────────────────────┘                └─────────────────────────┘
```

### 4.2 `document_hash` Ownership (Normative)

| Stage | Owner | Action |
|---|---|---|
| Document creation | e-Invoice Orchestration (document model) | Compute SHA-256 of canonical JSON **exactly once** |
| `submit` call | e-Invoice Orchestration | Pass `document_hash` in `SubmitFilingCommand` |
| `submit` execution | FilingGateway adapter | **Verify** hash matches recomputation; reject on mismatch (`E_HASH_MISMATCH`) |
| **Never** | FilingGateway adapter | Recompute-and-overwrite (would silently change legal document identity) |

**Rationale:** L0 §3.1 rule 2 — "The gateway verifies the supplied hash matches its recomputation and rejects on mismatch; it does not recompute-and-overwrite."

### 4.3 Token Lifecycle Encapsulation (Normative)

- **FilingGateway adapter** owns the 60-minute MyInvois token lifecycle (single-flight refresh, no second cache per L0 §3.1 rule 7)
- **No token material** crosses the boundary: not in `Command`, not in `Result`, not in `GatewayError`, not in `AuditRecord.redacted_detail`
- Orchestration has **zero knowledge** of token existence, expiry, or refresh

### 4.4 300KB Limit Enforcement (Normative)

- **FilingGateway adapter** enforces the limit on the serialized canonical JSON
- Error: `E_DOCUMENT_TOO_LARGE` with user-facing message including actual vs limit size
- Orchestration **should** pre-validate but **must not** rely on pre-validation (adapter is authority)

---

## 5. §7 Dependency Direction and Acyclicity Verification

### 5.1 Dependency Graph (L1 — Filing Vertical Slice)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DOMAIN MODULES                                      │
│  ┌─────────────────────┐    ┌─────────────────────────────────────────┐   │
│  │ e-Invoice           │    │ Ledger Core / Tax Engine /              │   │
│  │ Orchestration       │    │ Payroll Statutory / Compliance Calendar │   │
│  │                     │    │ (consume canonical types,               │   │
│  │ • CanonicalInvoice  │    │  produce CanonicalInvoiceDocument)      │   │
│  │   Document          │    │                                         │   │
│  │ • Command envelope  │    │                                         │   │
│  │ • Idempotency key   │    │                                         │   │
│  └──────────┬──────────┘    └─────────────────────────────────────────┘   │
│             │                                                             │
│             │ depends on (canonical types + gateway interfaces)          │
│             ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    GATEWAY INTERFACES                               │  │
│  │  FilingGateway.v1 (interface only — operations, shapes, errors)    │  │
│  │  + Canonical Types (TenantContext, ActorRef, CorrelationRef,      │  │
│  │    ConfidenceLabel, CanonicalField, Money, Quantity,              │  │
│  │    TaxPoint, PartyRef, DocumentRef, CanonicalInvoiceDocument,     │  │
│  │    FilingSubmissionResult, FilingStatusResult, AuditRecord)       │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│             ▲                                                             │
│             │ implements (adapter code only)                             │
│             │                                                             │
│  ┌──────────┴──────────────────────────────────────────────────────────┐ │
│  │                         ADAPTERS                                    │ │
│  │  FilingGateway Adapter                                              │ │
│  │  • Wraps existing filing service (ACCO-017/014/045)                │ │
│  │  • MyInvois SDK client                                             │ │
│  │  • Token lifecycle (60-min, single-flight refresh)                 │ │
│  │  • document_hash verification                                       │ │
│  │  • 300KB enforcement                                               │ │
│  │  • Duplicate detection / cancellation                              │ │
│  │  • Timeout → reconcile-only posture                                │ │
│  │  • AuditRecord emission (INV-4)                                    │ │
│  │  • Depends on: External Systems (MyInvois) + Canonical Types ONLY  │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│             │                                                             │
│             ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    EXTERNAL SYSTEMS                                 │  │
│  │  MyInvois (LHDN e-Invois) — REST API, OAuth2 client-credentials,   │  │
│  │  60-min tokens, SHA-256 documentHash, 300KB limit, UBL 2.1 JSON    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Dependency Direction Assertions (All Must Hold)

| # | Assertion | Verification |
|---|---|---|
| D1 | Domain Modules → Gateway Interfaces + Canonical Types | Orchestration imports only `FilingGateway.v1` interface + canonical types |
| D2 | Gateway Interfaces → Canonical Types only | `FilingGateway.v1` interface references only canonical types, no adapter code |
| D3 | Adapters → External Systems + Canonical Types | FilingGateway adapter imports MyInvois SDK + canonical types; **does not import** Orchestration |
| D4 | **No cycles** | Verified: no import path from Adapter → Orchestration → Gateway Interface → Adapter |
| D5 | FilingGateway adapter does not import Orchestration logic | Adapter is pure ACL; zero knowledge of Orchestration internal state |

### 5.3 INV-1 and INV-8 Validation at Boundary

| Invariant | Enforcement Point |
|---|---|
| INV-1: Tenant context in command | Orchestration constructs `Command.tenant`; FilingGateway validates present and matches idempotency namespace |
| INV-8: Timeout = reconcile-only | Orchestration **only** calls `reconcileAfterTimeout` on `E_EXTERNAL_TIMEOUT`; `submit` never retried; adapter `reconcileAfterTimeout` is read-only |

---

## 6. Extended Error Taxonomy (L1)

Inherits L0 §5 taxonomy and adds/clarifies for FilingGateway.v1 doc type 01:

| Code | Meaning | Origin | Retriable | Orchestration Action |
|---|---|---|---|---|
| `E_HASH_MISMATCH` | `document_hash` verification failed | L0 + L1 | No | Surface to user — document corrupted or tampered |
| `E_DOCUMENT_TOO_LARGE` | Canonical document > 300KB | L0 + L1 | No | Surface to user — reduce attachments/line items |
| `E_EXTERNAL_TIMEOUT` | MyInvois call timed out | L0 + L1 | **Reconcile only** | Call `reconcileAfterTimeout` with same idempotency key |
| `E_DOC_TYPE_UNSUPPORTED` | `doc_type` != "01" passed to L1 seam | L1 | No | Should be caught at Orchestration validation |
| `E_INVALID_DOCUMENT_STATE` | Document not in SUBMITTED state for status/reconcile | L1 | No | Surface — invalid operation for current state |
| `E_RECONCILE_FAILED` | `reconcileAfterTimeout` could not determine status | L1 | No | Escalate to compliance work item (manual follow-up) |

**Mapping to L0 codes:** L1 codes are **extensions**, not replacements. `E_HASH_MISMATCH`, `E_DOCUMENT_TOO_LARGE`, `E_EXTERNAL_TIMEOUT` exist in L0; L1 adds doc-type-specific semantics and two new codes.

---

## 7. Extended Idempotency Semantics (L1)

### 7.1 Namespace (Frozen from L0)

```
filing:<client_entity_id>:<caller_suffix>
```

- `<client_entity_id>`: UUID of the client entity (from `TenantContext.client_entity_id`)
- `<caller_suffix>`: Caller-chosen, ≤ 128 chars, recommended `crypto.randomUUID()`

### 7.2 Semantics for Doc Type 01

| Scenario | Behavior |
|---|---|
| First `submit` with key K | Execute filing; store (K, document_hash, result) |
| Retry `submit` with same key K, **same** document_hash | Return stored `FilingSubmissionResult` (idempotent success) |
| Retry `submit` with same key K, **different** document_hash | `E_IDEMPOTENCY_CONFLICT` — reject, do not overwrite |
| `submit` returns `E_EXTERNAL_TIMEOUT` | Caller **MUST** call `reconcileAfterTimeout` with **same** key K |
| `reconcileAfterTimeout` with key K | Query external status; return `FilingStatusResult`; **never** re-submit |
| `reconcileAfterTimeout` with different key | `E_VALIDATION` — key must match original `submit` |

### 7.3 Idempotency Key Generation (Orchestration Responsibility)

```
idempotency_key = "filing:" + tenant.client_entity_id + ":" + crypto.randomUUID()
```

- Generated **once** per filing attempt at Orchestration step 2
- Persisted with document for reconciliation path
- Never regenerated on retry — same key used for `reconcileAfterTimeout`

---

## 8. Extended Audit Hooks (L1)

### 8.1 `AuditRecord.interface_ref` Values (L1 Extension)

| Operation | `interface_ref` Value |
|---|---|
| `FilingGateway.v1.submit` | `FilingGateway.v1.submit` |
| `FilingGateway.v1.status` | `FilingGateway.v1.status` |
| `FilingGateway.v1.reconcileAfterTimeout` | `FilingGateway.v1.reconcileAfterTimeout` |

### 8.2 Required Fields (Per L0 §2.4 INV-4 + L1)

Every `AuditRecord` for FilingGateway operations **MUST** contain:

| Field | Source | Notes |
|---|---|---|
| `tenant_id` | `Command.tenant.tenant_id` | |
| `client_entity_id` | `Command.tenant.client_entity_id` | Nullable per L0 |
| `actor` | `Command.actor` | Full `ActorRef` |
| `correlation` | `Command.correlation` | Full `CorrelationRef` |
| `idempotency_key` | `Command.idempotency_key` | Namespaced `filing:...` |
| `external_ref` | `FilingSubmissionResult.submission_ref` or `FilingStatusResult.external_ref` | Nullable |
| `outcome` | Mapped from result/error | `AuditOutcome` enum |
| `duration_ms` | Adapter-measured | Wall-clock external call duration |
| `error_code` | `GatewayError.code` | L0/L1 taxonomy code |
| `redacted_detail` | Adapter-sanitized | **MUST NOT** contain token/cert/secret (INV-5) |

### 8.3 `ConfidenceLabel` Enforcement (INV-7)

- Every `CanonicalField` in `CanonicalInvoiceDocument` **MUST** carry `ConfidenceLabel`
- `AuditRecord` does not carry confidence (operation-level), but `FilingStatusResult.confidence` reflects reconciliation confidence
- Schema validation rejects any canonical type instance missing `confidence` field

---

## 9. Conformance Checklist (L1 Freeze Gate)

| # | Criterion | Status | Evidence |
|---|---|---|---|
| C1 | L1 document traces to frozen L0 canonical types (§2) | ☐ | §1.1 table |
| C2 | No new canonical types introduced | ☐ | §1.1 — all types from L0 |
| C3 | §7 dependency direction holds (D1–D5) | ☐ | §5.1 graph + §5.2 assertions |
| C4 | No implementation cycles | ☐ | §5.2 D4 |
| C5 | Error taxonomy extends L0 without breaking | ☐ | §6 table |
| C6 | Idempotency namespace `filing:` exclusive to FilingGateway | ☐ | §7.1 |
| C7 | Timeout = reconcile-only enforced at Orchestration | ☐ | §3.4 step 6, §5.3 |
| C8 | `document_hash` computed once by Orchestration, verified by Gateway | ☐ | §4.2 |
| C9 | Token lifecycle encapsulated in adapter (INV-5) | ☐ | §4.3 |
| C10 | 300KB limit enforced by adapter with `E_DOCUMENT_TOO_LARGE` | ☐ | §4.4 |
| C11 | Audit hooks extended with L1 `interface_ref` values | ☐ | §8.1 |
| C12 | All `AuditRecord` required fields present | ☐ | §8.2 |
| C13 | `ConfidenceLabel` schema-enforced on all canonical fields | ☐ | §8.3 |

---

## 10. Versioning and Freeze Policy

| Aspect | Policy |
|---|---|
| L1 version | `v0.1` (draft) → `v1.0` (frozen after Architecture Lead sign-off) |
| Breaking change | Increments minor version (`v1.1`, `v2.0`); absorbed in one adapter |
| Freeze trigger | Architecture Lead sign-off on this document |
| Post-freeze changes | Require new L1 version + Architecture Lead re-sign-off |
| Doc type scope | This L1 contract covers **doc type 01 only**; other doc types = new L1 slices |

---

## 11. Open Items for Architecture Lead Review

| # | Item | Question |
|---|---|---|
| O1 | Idempotency key suffix length | **Resolved:** 128-char suffix acceptable; UUID-only not mandated. Caller may use any 128-char string. |
| O2 | `reconcileAfterTimeout` polling interval | **Resolved:** Leave to Orchestration policy. L1 does not specify max retry duration/backoff. |
| O3 | `E_RECONCILE_FAILED` escalation | **Resolved:** Auto-create `ComplianceWorkItem` per L0 §2.3. Orchestration concern is the trigger, not the handler. |
| O4 | Confidence aggregation rule | **Resolved:** Min-aggregation. `CanonicalInvoiceDocument.confidence` = min of all field confidence labels, mapped VERIFIED > DERIVED > INFERRED > UNKNOWN. |
| O5 | `document_hash` algorithm | **Resolved:** SHA-256 hex frozen. Parameterization deferred to future L1 version with re-sign-off. |

---

## 12. Sign-off

| Role | Agent | Status | Reference |
|---|---|---|---|
| Author | Legacy Modernization Specialist (agent-9fde6dbd) | ✅ Draft complete | This document v0.1 |
| Architecture Lead | Architecture Lead (agent-7535016b) | ✅ **Signed off** | msg-a7626cc8, 26 Oct 2026 9:04 am — O1–O5 acceptable as described; per §12, L1 freeze proceeds |
| CTO | CTO (agent-0d8537a8) | ⏳ Not required | L1 freeze gate is Architecture Lead sign-off per §0 ownership split |

**Architecture Lead sign-off records:**
- **26 Oct 2026 9:04 am** — msg-a7626cc8 from agent-7535016b: "I have reviewed the L1 seam contract for the filing vertical slice. The open items (O1‑O5) are acceptable as described. Signing off per §12; you may proceed with the L1 freeze."
- **L1 seam contract FROZEN.** Implementation tasks (adapters, Orchestration wiring) may proceed with approved lineage M-MVN9TORT-000D-W0X7 → SL-MVNRWZPU-0005-2118 → F-MVNRX1RS-0006-XEXC.

---

*End of Document*