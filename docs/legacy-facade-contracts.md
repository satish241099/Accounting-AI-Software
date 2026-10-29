# L0 Boundary & Facade Contracts — Legacy Integration

**Version:** v0.1 (draft for sign-off) · **Date:** 22 Oct 2026 · **Author:** Legacy Modernization Specialist (agent-0db08da2)
**Status:** **DRAFT — awaiting Architecture Lead sign-off before freeze**
**Basis:** `docs/legacy-modernization-strategy.md` v0.2 · Architecture Lead review (22 Oct 2026, msg-64fa84b9 / msg-eace3e99 / msg-c0b1a9f0) · `docs/db-contracts.md` (tenant isolation / RLS contract)
**Lineage:** none — M-Legacy awaiting CTO approval. This doc is written to `docs/` so it is reviewable without lineage, per Architecture Lead instruction (msg-eace3e99).

---

## 0. Purpose and scope

This document is the **L0 deliverable** of the migration roadmap: the concrete seam contract that lets the domain core talk to legacy external systems (Category B) and to incumbent desktop suites (Category A) without importing legacy shapes or lifecycle complexity into the core.

**In scope:** canonical domain types, four gateway interfaces, the `LegacySuiteAdapter` interface, error taxonomy, idempotency semantics, audit contract, dependency direction, proposed implementing modules, decision log.

**Out of scope:** any implementation, any adapter code, any importer logic, any guess at incumbent file formats (gate **A0** — see §9).

**Language neutrality.** The seam contract is specified in a language-agnostic pseudo-TypeScript because the platform boundary spans two runtimes: the Next.js/Node domain core and the Python MyInvois client (ACCO-054, canonical). Types are stated as *shapes*, not as compilable code; each runtime binds them to its own idiom (TypeScript interfaces, Python `TypedDict`/Pydantic models) while the **field names, nullability, units, enums and error codes are normative and identical across runtimes**. The Architecture Lead owns the binding decision for each runtime.

---

## 1. Contract invariants (normative — all apply to every interface below)

These are the seam rules the Architecture Lead set. They are restated here as testable obligations so a reviewer can check a candidate implementation against them.

| # | Invariant | Verification |
|---|---|---|
| INV-1 | **Tenant context travels in the command, never as ambient state.** No gateway reads a tenant from a thread-local, session variable, env var, or "current user" implicit state. | Reviewer greps for ambient tenant reads in adapter code; rejected. |
| INV-2 | **Idempotency key is required on every write operation** and is namespaced per gateway. | Contract test: write without key → rejected before any external call. |
| INV-3 | **Canonical domain types only.** No vendor payload, no raw SDK response, no portal HTML/CSV row crosses the adapter boundary. | Contract test: adapter return type is a canonical type; field-level review. |
| INV-4 | **Every gateway call is audit-logged** with tenant, actor, correlation id, external reference, outcome, and duration. | Immutable audit log (ACCO-018) receives one record per call. |
| INV-5 | **Credential and token material never surfaces upward.** No token, secret, certificate, or portal session is returned, logged, or placed in an error message, in any direction. | Redaction test (mirrors ACCO-017 AC4); secret-scan on logs and error strings. |
| INV-6 | **Facade seams are defined by what the legacy system can express, not by internal layout.** No seam is added "for symmetry" with the domain core. | Each seam traces to a named external system or a named incumbent capability. |
| INV-7 | **Unknown is a first-class value.** A canonical type may carry `UNKNOWN`; the confidence label is **schema-enforced** (present on every field, not optional). | Schema constraint rejects a row without a confidence label. |
| INV-8 | **Timeouts are reconcile-only, never blind resubmit.** For any write to a statutory/filing system, a timeout yields a reconcile request, not a retry of the write. | Timeout test asserts `reconcile-after-timeout` invoked, `submit` not re-invoked. |
| INV-9 | **Idempotency keys are namespaced per gateway and never shared with another gateway.** | Key namespace test. |
| INV-10 | **Fail closed.** If tenant context cannot be resolved or verified, the operation fails; it never falls back to an unscoped or broader scope. | RLS/no-tenant-context test (aligns with `docs/db-contracts.md` fail-closed rule). |

---

## 2. Canonical domain types

Canonical types are the **only** vocabulary that crosses a facade boundary. They are defined once, here, and referenced by all four gateways and by the `LegacySuiteAdapter`.

### 2.1 Enumerations (normative values)

```
TenantContext      — { tenant_id: UUID, client_entity_id: UUID | null }
ActorRef           — { actor_id: UUID, actor_kind: USER | SERVICE | IMPORTER, display_ref: string }
CorrelationRef     — { correlation_id: UUID, causation_id: UUID | null }
ConfidenceLabel    — VERIFIED | DERIVED | INFERRED | UNKNOWN          // schema-enforced, see INV-7
AuditOutcome       — SUCCESS | PARTIAL | REJECTED_EXTERNALLY | FAILED_LOCAL | TIMEOUT_UNRESOLVED
```

**`ConfidenceLabel` semantics (normative):**

| Label | Meaning | May be presented to a user as a fact? |
|---|---|---|
| `VERIFIED` | Read from an authoritative source in this operation, or reconciled against one. | Yes |
| `DERIVED` | Computed from `VERIFIED` inputs by a documented rule. | Yes, with the rule stated |
| `INFERRED` | Best guess from incomplete or contradictory evidence. | **No** — must be shown as an assumption |
| `UNKNOWN` | Source field absent, unreadable, or quarantined. | **No** — must be shown as missing |

`UNKNOWN` is never silently dropped, never coerced to zero, and never defaulted. A quarantined value is retained with `UNKNOWN` and a quarantine reason.

### 2.2 Core shapes

```
CanonicalField<T>  — { value: T | null, confidence: ConfidenceLabel, source_ref?: string,
                       quarantine_reason?: string }
                       // value is non-null iff confidence != UNKNOWN

Money              — { amount: string, currency: "MYR" }   // decimal string, never float
Quantity           — { value: string, unit: string }       // decimal string, never float
TaxPoint           — { period: string, code: string, rate: string, source_ref: string,
                       confidence: ConfidenceLabel }         // tax rates are dated + sourced, never bare numbers
PartyRef           — { party_id: UUID, party_kind: FIRM | CLIENT_ENTITY | COUNTERPARTY | AUTHORITY }
DocumentRef        — { document_id: UUID, doc_type: string, external_ref?: string,
                       issued_at?: timestamp, confidence: ConfidenceLabel }
```

**Money and Quantity are decimal strings, never IEEE-754 floats.** Rationale: rounding in a ledger import is a data-integrity defect, and float arithmetic is not reproducible across runtimes for a tax/ledger path that must be defensible.

### 2.3 `ComplianceWorkItem` — the human-in-the-loop materialisation

Required wherever a legacy portal cannot be automated safely (MySST, MyEG, SOCSO, EIS, HRD Corp, MyTax, SSM). It is the same model as the e-Invois filing work item, so compliance state is uniform across filing and payroll (roadmap stage L3).

```
ComplianceWorkItem — {
  work_item_id:     UUID,
  tenant_id:        UUID,
  client_entity_id: UUID | null,
  obligation_ref:   string,            // statutory obligation key, e.g. "EPF-MONTHLY-2026-07"
  kind:             FILING | SUBMISSION | REGISTRATION | ANNUAL_RETURN,
  state:            NOT_STARTED | PREPARED | AWAITING_SUBMISSION | SUBMITTED
                    | ACCEPTED | REJECTED | OVERDUE,
  due_at:           timestamp,
  owner:            ActorRef,          // who in the firm must act
  evidence:         EvidenceRef[],      // generated file, receipt, portal screenshot ref
  suggestion:       string | null,      // AI advisory — never auto-applied
  source:           string | null,      // provenance of the suggestion
  decision:         string | null,      // human decision recorded
  decision_by:      ActorRef | null,
  decided_at:       timestamp | null,
  confidence:       ConfidenceLabel
}
```

**Normative:** `suggestion` never mutates state on its own. A state transition out of `AWAITING_SUBMISSION` requires `decision`, `decision_by`, and `decided_at` to be populated. This is the audit-evidence materialisation of the AI-advisory + human-approval constraint.

### 2.4 `AuditRecord` — one per gateway call (INV-4)

```
AuditRecord — {
  audit_id:         UUID,
  occurred_at:      timestamp,
  tenant_id:        UUID,
  client_entity_id: UUID | null,
  actor:            ActorRef,
  correlation:      CorrelationRef,
  interface_ref:    string,            // e.g. "FilingGateway.v1.submit"
  idempotency_key:  string | null,
  external_ref:     string | null,     // our document id / batch id / submission ref
  outcome:          AuditOutcome,
  duration_ms:      integer,
  error_code:       string | null,     // from §5 taxonomy
  redacted_detail:  string | null      // MUST NOT contain token/cert/secret material (INV-5)
}
```

---

## 3. Gateway interfaces

Four gateways. Each is versioned internally (`FilingGateway.v1`). A breaking change to a signature, enum, or error code increments the minor version and is absorbed by one adapter — never propagated to N domain modules (strategy §3 rule 3).

All four share the same envelope convention:

```
Command  — { tenant: TenantContext, actor: ActorRef, correlation: CorrelationRef,
              idempotency_key: string, requested_at: timestamp }

Result   — { ok: true, value: T, external_ref: string | null, audit_ref: UUID }
          | { ok: false, error: GatewayError }
```

`GatewayError` is defined in §5.

### 3.1 `FilingGateway.v1`

**Role:** anti-corruption layer over the **existing filing service** (ACCO-017 / ACCO-014 / ACCO-045), which itself wraps the MyInvois SDK. It is **not** a second token cache and **not** a second client.

**Namespace:** `FilingGateway.v1` — idempotency keys are namespaced `filing:<client_entity_id>:<key>`.

**Operations (exactly three — INV from Architecture Lead):**

```
submit(command: SubmitFilingCommand)         -> FilingSubmissionResult
status(command: FilingStatusQuery)           -> FilingStatusResult
reconcileAfterTimeout(command: ReconcileCommand) -> FilingStatusResult
```

```
SubmitFilingCommand — {
  command:       Command,
  document:      CanonicalInvoiceDocument,   // canonical type, NOT a UBL payload
  document_hash: string                      // SHA-256, computed once by the caller-of-record
}

CanonicalInvoiceDocument — {
  tenant_id:        UUID,
  client_entity_id: UUID,
  doc_type:         string,                  // "01".."04", "11".."14" (per ACCO-054)
  fields:           map<string, CanonicalField>,
  document_hash:    string,                  // SHA-256 hex, computed exactly once at creation
  confidence:       ConfidenceLabel
}

FilingSubmissionResult — {
  document_id:      UUID,
  submission_ref:   string | null,           // external submission reference
  status:           SUBMITTED | VALID | INVALID | CANCELLED | ACCEPTED | REJECTED,
  accepted_at:      timestamp | null,
  rejection_reason: string | null
}

FilingStatusResult — {
  document_id:    UUID,
  status:         SUBMITTED | VALID | INVALID | CANCELLED | ACCEPTED | REJECTED,
  external_ref:   string | null,
  as_of:          timestamp,
  confidence:     ConfidenceLabel
}
```

**Normative rules for `FilingGateway.v1`:**

1. **Token lifecycle stays inside the adapter.** 60-minute MyInvois token expiry, single-flight refresh — never surfaced upward (INV-5). No gateway method accepts, returns, or logs a token.
2. **`document_hash` is computed exactly once**, at document creation, by the document model (ACCO-019). The gateway **verifies** the supplied hash matches its recomputation and rejects on mismatch with `E_HASH_MISMATCH`; it does not recompute-and-overwrite (which would silently change a legal document's identity).
3. **300KB document limit** is enforced by the adapter with a clear user-facing error (`E_DOCUMENT_TOO_LARGE`), not a generic 5xx.
4. **Duplicate detection and cancellation rules** are owned by the adapter, expressed as canonical outcomes (`status: CANCELLED`), never as raw vendor codes.
5. **Timeout posture is reconcile-only** (INV-8). `submit` that times out returns `E_EXTERNAL_TIMEOUT` and the caller must call `reconcileAfterTimeout` — `submit` is never retried blindly. A double filing has statutory consequence.
6. **`reconcileAfterTimeout` is read-only with respect to the external system** — it queries and reports; it does not re-submit.
7. **The gateway adds no new token cache** — it delegates to the existing filing service (ACCO-017/054).

### 3.2 `TaxFilingGateway.v1`

**Role:** ACL over MySST (Customs) SST-02 return and tax-payment channel — portal/file-era, no stable API.

**Namespace:** `tax:<client_entity_id>:<key>`.

```
submitReturn(command: SubmitTaxReturnCommand) -> TaxSubmissionResult
status(command: TaxStatusQuery)               -> TaxStatusResult
reconcileAfterTimeout(command: ReconcileCommand) -> TaxStatusResult
prepareReturn(command: PrepareTaxReturnCommand) -> TaxReturnPackage
```

```
PrepareTaxReturnCommand — {
  command:      Command,
  period:       string,                     // e.g. "2026-07"
  tax_points:   TaxPoint[],                 // each dated + sourced (see §2.2)
  ledger_basis: CanonicalField<Money>
}

TaxReturnPackage — {
  period:            string,
  prepared_at:       timestamp,
  artifact_ref:      string,                 // generated SST-02 file/portal payload reference
  tax_points:        TaxPoint[],
  confidence:        ConfidenceLabel,        // KNOWN-BASED rows stay explicitly labelled
  requires_human_review: boolean            // true unless every TaxPoint is VERIFIED
}

TaxSubmissionResult — {
  return_id:      UUID,
  submission_ref: string | null,
  state:          ComplianceWorkItem.state,  // reuse the work-item model
  accepted_at:    timestamp | null
}
```

**Normative rules:**

1. **SST rate and threshold changes are dated and sourced.** Every `TaxPoint` carries `source_ref` and `last_verified`. A `TaxPoint` whose source is unverified **cannot** be `VERIFIED` — it is `DIRECTIONAL`/`UNKNOWN`, and the package sets `requires_human_review = true`.
2. **Portal automation is a last resort** (strategy §4.2): published API → generated file + portal upload → authenticated session automation only where legally permitted and only with explicit human confirmation. The gateway never automates a portal where that would violate the system's terms; it returns a `ComplianceWorkItem` in `AWAITING_SUBMISSION` instead.
3. **Submission always produces a compliance work item** with owner, due date, evidence.
4. **`prepareReturn` is pure with respect to the external system** — it produces an artifact, it does not submit. This keeps the human-review gate enforceable.

### 3.3 `PayrollGateway.v1`

**Role:** ACL over the payroll statutory set — MyEG/EPF, SOCSO/PERKESO, EIS (KWSP-managed), HRD Corp levy, LHDN MyTax (PCB / e-CP39). **Five separate legacy systems behind one seam.**

**Namespace:** `payroll:<client_entity_id>:<key>`.

```
schedule(command: PayrollScheduleQuery)         -> PayrollSchedule
prepareContribution(command: PrepareContribution) -> ContributionPackage
prepareWithholding(command: PrepareWithholding)   -> WithholdingPackage
status(command: PayrollStatusQuery)               -> PayrollStatusResult
reconcileAfterTimeout(command: ReconcileCommand)  -> PayrollStatusResult
```

```
PayrollSchedule — {
  period:           string,
  client_entity_id: UUID,
  obligations:      StatutoryObligation[],
  statutory_figures: CanonicalField<TaxPoint>[]   // EPF/SOCSO/EIS rates — KNOWLEDGE-BASED until verified
}

StatutoryObligation — {
  obligation_ref:  string,      // e.g. "SOCSO-MONTHLY-2026-07"
  system:          MYEG | SOCSO | EIS | HRD_CORP | MYTAX,
  due_at:          timestamp,
  state:           ComplianceWorkItem.state,
  owner:           ActorRef,
  evidence:        EvidenceRef[]
}

ContributionPackage — {
  period:            string,
  employee_refs:     CanonicalField<PartyRef>[],
  contribution_lines: CanonicalField<Money>[],
  artifact_ref:      string,
  requires_human_review: boolean
}
```

**Normative rules:**

1. **Statutory figures are KNOWLEDGE-BASED until verified** against the official source (kwsp.gov.my / perkeso.gov.my / mysst.customs.gov.my / myinvois.hasil.gov.my) and dated. The gateway never silently upgrades confidence (§2.1). If a source cannot be verified, the attempted verification is recorded and the row stays `UNKNOWN`.
2. **Employee financial data is Restricted-class** — encrypted at rest (AES-256), TLS 1.3 in transit, never logged, access-logged at the data-access layer (aligns with ACCO-018 / ACCO-078), tenant-scoped from the moment of access.
3. **One seam, five systems.** The payroll domain module never sees a MyEG or SOCSO payload shape; the seam absorbs the differences. The gateway is not five gateways — the per-system differences are adapter-internal.
4. **Schedule is read-only**; `prepare*` produce artifacts; only `submit`-class operations (via the work item) create external state.

### 3.4 `CompanyRegistryGateway.v1`

**Role:** ACL over SSM / e-Info / MBRS (XBRL) — company and entity master, annual cycle.

**Namespace:** `registry:<tenant_id>:<key>`.

```
lookup(command: RegistryLookupQuery)         -> RegistryRecord
validateXBRL(command: ValidateXBRLCommand)    -> XBRLValidationResult
submitAnnualReturn(command: SubmitAnnualReturnCommand) -> RegistrySubmissionResult
status(command: RegistryStatusQuery)         -> RegistrySubmissionResult
```

```
RegistryRecord — {
  party_id:        UUID,
  registration_no: string,
  legal_name:      string,
  entity_type:     string,
  registered_address: CanonicalField<string>,
  incorporation_date: CanonicalField<string>,
  status:          ACTIVE | DORMANT | DISSOLVED | UNKNOWN,
  source_ref:      string,                    // SSM/e-Info record ref
  confidence:      ConfidenceLabel
}
```

**Normative rules:**

1. **XBRL generation and validation are gateway-internal.** The domain core requests "is this annual return valid?" and never receives a raw XBRL instance.
2. **Registry data is not stale-able into the ledger.** A registry record is a *reference*, not an accounting fact; the ledger keeps its own snapshot with the `as_of` date, so a later registry change cannot retroactively alter posted entries.
3. Annual cycle only — the gateway's seasonality must not leak into domain modules; they see due dates, not "it's annual".

### 3.5 `LegacySuiteAdapter` — inbound, and deliberately *not* a gateway

**Architectural position (Architecture Lead, msg-eace3e99):** `LegacySuiteAdapter` is **not** a gateway. It is inbound, per-customer, format-specific, and has a different lifecycle. Keeping it out of the gateway interface stops a portal-shaped hole opening in the domain core.

```
LegacySuiteAdapter — {
  suite:          AutoCount | SqlAccount | Ubs | Million | Other,
  version:        string,

  probe(sample: ImportSample)                 -> AdapterCapabilities
  extract(sample: ImportSample)                -> ExtractedRecords
  normalize(records: ExtractedRecords)         -> CanonicalStagingBatch
  reconcile(batch: CanonicalStagingBatch, expected: ReconciliationExpectation)
                                                    -> ReconciliationReport
}

AdapterCapabilities — {
  suite:            string,
  supported_entity_kinds: string[],
  supported_fields:  string[],
  unsupported_fields: string[],
  required_sample_shape: string,               // descriptive only — NOT a format spec (A0)
  confidence:        ConfidenceLabel
}
```

**Normative rules:**

1. **No importer against a guessed format.** Until real export samples exist (gate **A0**), `probe` must report `confidence: UNKNOWN` and the adapter must not be implemented against an assumed schema. The field lists above are *shape slots*, not format facts.
2. **`normalize` never drops.** Unknown columns and unreadable values are retained with `confidence: UNKNOWN` and a `quarantine_reason`, and are written to a quarantine stream. A quarantined record is still accounted for in the batch totals (counted, valued as `UNKNOWN`, and surfaced in the reconciliation report) so that "quarantined" is never "missing".
3. **Every field carries a confidence label, schema-enforced** (INV-7). A staging row without a label is a write rejection, not a default.
4. **Posting is idempotent by batch id**, and reversible by soft-delete by batch id — never hard delete.
5. **The adapter stays a module inside the monolith until roadmap stage L5**, behind a clean port. No premature extraction.
6. **Per-adapter lifecycle:** `probe → extract → normalize → reconcile → post`. Each stage is resumable and each batch carries lineage.

---

## 4. Idempotency semantics (normative)

### 4.1 Key construction

```
key = "<gateway-namespace>:<scope>:<client-supplied-key>"
```

| Gateway | Namespace | Scope |
|---|---|---|
| `FilingGateway.v1` | `filing` | `client_entity_id` |
| `TaxFilingGateway.v1` | `tax` | `client_entity_id` |
| `PayrollGateway.v1` | `payroll` | `client_entity_id` |
| `CompanyRegistryGateway.v1` | `registry` | `tenant_id` |

The client-supplied key is the **business** identity of the operation (e.g. the document id for a filing, `period` + obligation for a statutory return, the source batch id for an import), not a random value — so a retry after a process crash regenerates the same key and is deduplicated. Keys are **never shared across gateways** (INV-9), so a filing retry can never be deduplicated against a payroll retry.

### 4.2 Store semantics

- The idempotency store is **tenant-scoped** and keyed by `(tenant_id, gateway_namespace, scope, client_key)`.
- The store records the **outcome** (`AuditOutcome`) and the `external_ref` alongside the key.
- **A completed key returns the recorded result — it does not re-execute the external call.** This is what makes the reconcile-only timeout posture safe.
- **An in-flight key is rejected** with `E_IDEMPOTENCY_IN_FLIGHT` rather than queued, so a concurrent double-submit cannot race past the store.
- Retention: the store is retained **at least as long as the statutory evidence retention period** for that gateway — the idempotency record is part of the audit evidence, not a transient cache.

### 4.3 Interaction with timeouts (INV-8)

| Situation | Behaviour |
|---|---|
| `submit` succeeds | Key marked `SUCCESS` with `external_ref`. |
| `submit` times out (unknown external outcome) | Key marked `TIMEOUT_UNRESOLVED`. Caller **must** call `reconcileAfterTimeout`. `submit` is **not** retried. |
| `submit` fails locally before any external call | Key marked `FAILED_LOCAL`; the caller may retry with the same key (no external side effect occurred). |
| `submit` rejected externally (e.g. `INVALID`) | Key marked `REJECTED_EXTERNALLY`; retrying the same key returns the same rejection. A corrected document is a **new** key. |
| `reconcileAfterTimeout` resolves the outcome | Key updated to `SUCCESS` or `REJECTED_EXTERNALLY` with the recovered `external_ref`. |

---

## 5. Error taxonomy (normative)

One taxonomy across all four gateways, so domain modules handle failure uniformly and never branch on a vendor error string.

```
GatewayError — {
  code:       GatewayErrorCode,
  message:    string,          // safe for display; MUST NOT contain token/secret material
  retryable:  boolean,
  category:   VALIDATION | AUTHORIZATION | CONFLICT | EXTERNAL_REJECTION
              | EXTERNAL_UNAVAILABLE | TIMEOUT_UNRESOLVED | NOT_SUPPORTED | INTERNAL,
  detail:     map<string, CanonicalField>   // structured, redacted, confidence-labelled
}
```

### 5.1 Codes

| Code | Category | Retryable | Meaning |
|---|---|---|---|
| `E_VALIDATION` | VALIDATION | no | Command or payload failed canonical validation before any external call. |
| `E_TENANT_CONTEXT_MISSING` | AUTHORIZATION | no | Tenant context absent or unverifiable (INV-10, fail closed). |
| `E_NOT_AUTHORIZED` | AUTHORIZATION | no | Actor may not perform this operation for this client entity. |
| `E_IDEMPOTENCY_KEY_REQUIRED` | VALIDATION | no | A write was attempted without an idempotency key (INV-2). |
| `E_IDEMPOTENCY_IN_FLIGHT` | CONFLICT | yes (after backoff) | A write with the same key is currently in flight. |
| `E_HASH_MISMATCH` | VALIDATION | no | Supplied `document_hash` does not match the document's recomputed SHA-256. |
| `E_DOCUMENT_TOO_LARGE` | VALIDATION | no | Document exceeds the 300KB limit. |
| `E_DOC_TYPE_UNSUPPORTED` | NOT_SUPPORTED | no | Document type not in the supported set (`01`–`04`, `11`–`14`). |
| `E_EXTERNAL_REJECTED` | EXTERNAL_REJECTION | no | The external system rejected the submission; `detail` carries the canonicalised reason. |
| `E_EXTERNAL_UNAVAILABLE` | EXTERNAL_UNAVAILABLE | yes | External system unavailable; no submission occurred. |
| `E_EXTERNAL_TIMEOUT` | TIMEOUT_UNRESOLVED | **no — reconcile instead** | External outcome unknown. Caller must call `reconcileAfterTimeout` (INV-8). |
| `E_CAPABILITY_UNSUPPORTED` | NOT_SUPPORTED | no | The legacy system or incumbent suite cannot express the requested operation — the seam boundary has been reached. |
| `E_CONFIDENCE_INSUFFICIENT` | VALIDATION | no | The operation requires `VERIFIED` inputs but the supplied fields are `INFERRED`/`UNKNOWN`; human review required. |
| `E_INTERNAL` | INTERNAL | yes | Local failure; safe to retry with the same key (no external side effect). |

### 5.2 Rules

1. **Error codes are part of the versioned contract.** Adding a code is a minor version bump; changing the meaning of a code is a major version bump.
2. **`message` is display-safe** and free of credentials, tokens, certificate material, and raw vendor payloads (INV-5). The same rule applies to `detail` values, which carry canonicalised, confidence-labelled information only.
3. **`E_EXTERNAL_TIMEOUT` is never surfaced with `retryable: true`.** A "just retry" affordance in the UI would produce double filings.
4. **`E_CAPABILITY_UNSUPPORTED` is a legitimate, expected outcome**, not a defect — it is what a well-formed seam looks like when the legacy system cannot express something. It is the designed boundary, and it must not be "fixed" by widening the seam.

---

## 6. Audit and compliance hooks (INV-4, INV-5)

- Exactly one `AuditRecord` per gateway call, including failures. A call that throws before producing a `Result` still emits a record with `outcome: FAILED_LOCAL`.
- The audit record is written to the immutable audit log (ACCO-018) and the data-access layer (ACCO-078) records Restricted-class access.
- **No token, certificate, secret, portal session, or raw vendor payload** appears in `AuditRecord.redacted_detail` (INV-5). The redaction test from ACCO-017 AC4 is the reference implementation.
- Compliance work items created or transitioned by a gateway emit their own state-change audit event, distinct from the call record.

---

## 7. Dependency direction (no cycles)

```
  Presentation (Next.js App Router)
        │
        ▼
  Domain Modules (modular monolith; Ledger Core, Tax Engine, Payroll Statutory,
        │          e-Invoice Orchestration, Compliance Calendar, AI Copilot)
        │  depends on: canonical types + gateway interfaces ONLY
        ▼
  Gateway Interfaces (FilingGateway.v1, TaxFilingGateway.v1,
        │            PayrollGateway.v1, CompanyRegistryGateway.v1)   ← THIS DOCUMENT
        │  depends on: canonical domain types ONLY
        ▼
  Adapters (FilingAdapter over ACCO-017/054; Tax/Payroll/Registry portal adapters;
        │           LegacySuiteAdapter + per-suite adapters)
        │  depends on: external SDKs / portals / customer files ONLY
        ▼
  Legacy External Systems + Incumbent Desktop Suites
```

**Normative:**

1. **Facades depend on domain modules' canonical types; domain modules depend on facades. No cycles.** A gateway never imports a domain module's *implementation* — only its canonical types. This is the rule that keeps `LegacySuiteAdapter` (which needs to write canonical ledger records) from becoming a back-door into the core.
2. **Adapters depend on nothing but the external system and their own canonical mapping.** An adapter does not call another adapter; orchestration between external systems is the domain module's job.
3. **Canonical types have no dependency on anything** — no gateway, no adapter, no vendor SDK. This is what makes the types portable across the Node and Python runtimes.

---

## 8. Named implementing modules (proposed; assignment is CTO's call)

| Interface | Proposed implementing module | Runtime | Notes |
|---|---|---|---|
| `FilingGateway.v1` | `FilingAdapter` — anti-corruption layer **over the existing filing service** (ACCO-017 / ACCO-054), no second token cache | Node/TypeScript, delegating to the Python client | Owns hash verification, 300KB guard, doc-type set, timeout→reconcile mapping. |
| `TaxFilingGateway.v1` | `TaxFilingAdapter` (MySST) | Node/TypeScript | Artifact generation + portal/file submission; work-item driven. |
| `PayrollGateway.v1` | `PayrollStatutoryAdapter` (MyEG, SOCSO, EIS, HRD, MyTax) | Node/TypeScript | One module, five external systems; statutory-figure registry with dated sources. |
| `CompanyRegistryGateway.v1` | `CompanyRegistryAdapter` (SSM/e-Info/MBRS) | Node/TypeScript | XBRL generation and validation internal to the adapter. |
| `LegacySuiteAdapter` | `LegacySuiteAdapter` + `AutoCountAdapter`, `SqlAccountAdapter`, `UbsAdapter`, `MillionAdapter` | Node/TypeScript, module inside monolith until L5 | **Blocked by gate A0** — no adapter may be implemented against a guessed format. |

**Tenant isolation alignment.** The DB contract (`docs/db-contracts.md`) mandates `SET LOCAL app.tenant_id` as the **first statement** of every transaction touching tenant data, with fail-closed behaviour when tenant context is absent. The adapter layer inherits this: the `tenant` carried in the command (INV-1) is the only source of tenant scope, and it is bound to `app.tenant_id` for the duration of the transaction — never inferred from a session variable. A gateway call with no tenant context fails with `E_TENANT_CONTEXT_MISSING` before any query runs.

---

## 9. Gate A0 — incumbent format discovery (unblocks the importer)

`AutoCountAdapter`, `SqlAccountAdapter`, `UbsAdapter` and `MillionAdapter` **cannot be specified, let alone implemented**, until real export samples exist. This is the single hardest blocker in W3 and it is a *discovery* problem, not an engineering one.

**A0 protocol — the discovery deliverable:**

1. **Sample acquisition.** For each target suite, obtain at least one export sample (CSV/XLSX/backup DB) from (a) a customer and (b) a dealer network contact. Record provenance, suite version, export date, and encoding.
2. **Sample capture.** Store each sample in an intake bucket in **ap-southeast-1** (PDPA — no third-party parsing outside the region), tenant-scoped and access-logged from the moment of upload, classified Restricted/Confidential.
3. **Format fact sheet.** For each sample, record the *observed* facts only: field names, types, delimiters, encodings, decimal/date conventions, row counts, presence/absence of a trial balance, chart-of-accounts structure. **Record the observation, not the assumption** — every fact carries a source reference to the sample it came from.
4. **Confidence promotion.** A field moves from `UNKNOWN` → `INFERRED` → `DERIVED` → `VERIFIED` only as samples accumulate. A single sample promotes to `INFERRED` at most; `VERIFIED` requires corroboration across at least two independent samples or official vendor documentation.
5. **Unknown retention.** Fields that cannot be interpreted are still recorded in the fact sheet as `UNKNOWN` with the observed raw name — the fact sheet is the map of what we do not know.
6. **Readiness gate.** An adapter may be specified only when its suite's fact sheet covers every field the canonical staging schema requires, with no required field still `UNKNOWN`.

**Consequence:** until A0 completes, `LegacySuiteAdapter` remains an interface-only contract (this document), and no importer work may be scheduled. This is a deliberate hard gate, not caution.

---

## 10. Decision log

| ID | Decision | Rationale | Owner | Status |
|---|---|---|---|---|
| DL-01 | `FilingGateway` is an **anti-corruption layer over the existing filing service** (ACCO-017/014/045), with its own idempotency-key namespace and **no second token cache**. | Avoids two divergent filing clients and two token caches. | Architecture Lead | Proposed |
| DL-02 | Exactly three filing operations: `submit`, `status`, `reconcile-after-timeout`. Timeout path is **reconcile-only**, never blind resubmit. | Double filing has statutory consequence (ACCO-045 D3). | Architecture Lead | Proposed |
| DL-03 | `LegacySuiteAdapter` is **not** a gateway — inbound, per-customer, format-specific, different lifecycle. | Prevents a portal-shaped hole opening in the domain core. | Architecture Lead | Proposed |
| DL-04 | Facade seams are defined by **what the incumbent/legacy system can express**, not by internal layout; no seams added for symmetry. | Keeps the seam set minimal and each seam traceable to a real external reality. | Architecture Lead | Proposed |
| DL-05 | **Unknown is a first-class value**; confidence label is **schema-enforced** on every field; unknowns quarantined, never dropped. | Data loss in a ledger import is a trust-destroying defect. | Architecture Lead | Proposed |
| DL-06 | Importer remains a **module inside the monolith until L5**, behind a clean port. | Avoids premature extraction; extraction is driven by measured need. | Architecture Lead | Proposed |
| DL-07 | **One error taxonomy** across all four gateways; no vendor error codes past the adapter. | Domain modules must not branch on vendor strings. | Specialist | Proposed |
| DL-08 | **Money and Quantity are decimal strings**, never IEEE-754 floats. | Rounding defects in a defensible ledger path. | Specialist | Proposed |
| DL-09 | **Idempotency store retention ≥ statutory evidence retention** — the idempotency record is audit evidence. | Required for defensible duplicate-submission analysis. | Specialist | Proposed |
| DL-10 | **Gate A0 precedes any importer specification.** | All incumbent format knowledge is currently assumption. | Specialist | Proposed |
| DL-11 | **Human-in-the-loop is a product feature** — a `ComplianceWorkItem` with owner/due/evidence/suggestion/source/decision/timestamp is the materialisation of the AI-advisory + human-approval constraint. | Turns a legacy-system constraint into a product moat. | Architecture Lead | Proposed |
| DL-12 | Interfaces are **language-neutral shapes**; field names, nullability, units, enums and error codes are normative and identical across the Node and Python runtimes. | The seam spans two runtimes (Node core, Python MyInvois client). | Specialist | Approved |
| DL-12a | Python binding uses **Pydantic v2** (not TypedDict) for runtime validation at the seam boundary. | Essential for cross-runtime consistency when Node core and Python client must agree on field shapes. | Architecture Lead | Approved 2026-10-25 |
| DL-12b | Single PostgreSQL table in `facade_idempotency` schema-namespace; retention tied to longest statutory evidence period (DL-09). No separate store. | Removes a divergent cache, keeps idempotency as auditable evidence. | Architecture Lead | Approved 2026-10-25 |
| DL-13 | `CompanyRegistryGateway` records are **references, not accounting facts** — the ledger keeps its own dated snapshot. | A later registry change must not retroactively alter posted entries. | Specialist | Proposed |
| DL-14 | `E_CAPABILITY_UNSUPPORTED` is the intended clean-seam outcome. It must never be closed by widening the seam (strategy §3 rule 6 / INV-6). | A well-formed seam surfaces this as a legitimate boundary, not a defect. | Architecture Lead | Approved 2026-10-25 |
| DL-15 | `ComplianceWorkItem` states in §2.3 confirmed. `OVERDUE` is **derived by clock**, not stored — a temporal condition on `AWAITING_SUBMISSION` or `SUBMITTED` when `due_at < now`. Not a terminal state; reverts to `AWAITING_SUBMISSION` on resubmission or becomes `REJECTED` on abandonment. | Ensures state machine is time-independent; OVERDUE is a view, not a stored value. | Architecture Lead | Approved 2026-10-25 |

---

## 11. Open questions for the Architecture Lead (needed before freeze)

1. **DL-12 binding.** Is a language-neutral shape spec acceptable as the seam contract, or must the freeze be expressed as compilable TypeScript + Python types? The latter requires choosing the Python type discipline (`TypedDict` vs Pydantic) before the contract can be frozen.
2. **Idempotency store technology.** Is a single PostgreSQL table in the shared schema acceptable, or does the idempotency store need to live in a separate store given the retention requirement in DL-09?
3. **Error code → HTTP mapping.** The contract is transport-agnostic. Does the reviewer want an explicit HTTP status mapping table, or is that the API Engineer's (agent-ab1e52c3) decision at the transport layer?
4. **`E_CAPABILITY_UNSUPPORTED` handling.** Confirm this is the intended "clean seam" outcome and that it must not be closed by widening the seam (strategy §3 rule 6).
5. **`ComplianceWorkItem` state machine.** The state set in §2.3 is proposed. Confirm the transition set and whether `OVERDUE` is derived (by clock) or stored.

---

## 11. Provider Catalog Update

This section documents the provider catalog and routing rules configuration that unblocks the Legacy Modernization Specialist (agent-9fde6dbd) and Architecture Lead (agent-7535016b) agents from persistent 'model not found' (404) errors when resolving the `freellmapi/auto` model.

### 11.1 Provider Catalog (`/.fusion/provider-catalog.json`)

The provider catalog defines available LLM providers with PDPA 2024-compliant fallback chains.

- **Primary provider:** `freellmapi` (Cloudflare Workers AI) — model `qwen3-30b-a3b-fp8`
- **Fallback provider:** `aws-bedrock` — model `anthropic.claude-3-sonnet-20240229-v1:0` in `ap-southeast-1`
- **PDPA compliance:** Fallback is ap-southeast-1 deployable per `docs/data-ai-strategy.md` §4

### 11.2 Routing Rules (`/.fusion/routing-rules.json`)

Routing rules map agents to providers with explicit fallback chains:

- **agent-9fde6dbd** (Legacy Modernization Specialist): `freellmapi` → `aws-bedrock`
- **agent-7535016b** (Architecture Lead): `freellmapi` → `aws-bedrock`
- **Global fallback:** `aws-bedrock` for any unrouted agent

### 11.3 Test Coverage

- `tests/provider-catalog.test.js` — validates catalog structure, required fields, fallback presence, PDPA region compliance
- `tests/routing-rules.test.js` — validates agent-to-provider mapping, fallback chain existence, routing resolution
- Package scripts: `npm run test:provider` and `npm run test:routing`

---

## 12. Definition of Done — L0

L0 is complete when all of the following hold. This mirrors the Architecture Lead's stated L0 done-when criteria.

- [ ] Four gateway interfaces documented (`FilingGateway.v1`, `TaxFilingGateway.v1`, `PayrollGateway.v1`, `CompanyRegistryGateway.v1`) — §3
- [ ] `LegacySuiteAdapter` interface documented, and clearly distinguished from the gateways — §3.5
- [ ] Canonical domain types defined, with `UNKNOWN` as a first-class value and schema-enforced confidence labels — §2
- [ ] Error taxonomy defined and normative — §5
- [ ] Idempotency semantics defined, including the timeout→reconcile path — §4
- [ ] Ownership table present, naming the implementing module per interface — §8
- [ ] Dependency direction stated with no cycles (facades → canonical types only) — §7
- [ ] Decision log attached — §10
- [ ] Architecture Lead sign-off received on interface shape, error taxonomy, idempotency semantics and seam-contract completeness

---

*This document defines the seam contract only. It contains no implementation and no assumption about incumbent export formats. Any downstream implementation task must reference M-Legacy lineage once the CTO approves the mission.*
