# Legacy Modernization & Migration Strategy — Malaysia Accounting SaaS

**Version:** v0.2 · **Date:** 22 Oct 2026 · **Author:** Legacy Modernization Specialist (agent-0db08da2)
**Status:** Proposal for Architecture Lead sign-off — input to the main Architecture & Compliance Design Doc
**Basis:** `docs/competitive-analysis.md` v0.1, project memory (`MEMORY.md`), verified MyInvois SDK facts (21 Oct 2026), Architecture Lead review §3/§7/§9 (22 Oct 2026)

---

## 0. TL;DR for the CTO

The workspace has **no codebase** — this is greenfield. So there is no monolith of ours to decompose *yet*. But "legacy" is present in two forms that will shape the architecture if we ignore them at design time:

1. **Legacy *data* we must ingest** (incumbent desktop suites: AutoCount, SQL Account, UBS, Million). Switching cost is the #1 wedge opportunity (W3) *and* the #1 onboarding failure mode.
2. **Legacy *external systems* we must integrate** (portal-era government systems: MySST, MyEG/EPF, SOCSO, SSM/e-Info, MyTax). These are portal-first, batch-file-era systems that are legacy by construction, and they are the ones with legal filing deadlines attached.

**Recommendation:** adopt **branch-by-abstraction for our own domain modules** and **strangler-fig + anti-corruption layer (ACL) facades for every legacy external system**, with a single **Migration Importers** boundary (W3) that converts legacy data into canonical ledger records rather than importing legacy *shapes* into the core.

**Asks of the CTO (2):**
- Approve a **Mission M-Legacy "Legacy Integration & Migration Boundaries"** with 2 slices (see §7) so downstream tasks can carry approved lineage.
- Confirm ownership split with the **Architecture Lead**: I propose owning the *boundary/facade contracts + migration roadmap*; Architecture Lead owns internal service decomposition and event topology. **Seam contract (interface shape, error taxonomy, idempotency) is jointly owned — I propose, Architecture Lead signs off before freeze.**

---

## 1. Legacy Landscape Map

### 1.1 Category A — Incumbent desktop accounting suites (legacy data sources)

| Suite | Position | Legacy character | Migration relevance | Evidence status |
|---|---|---|---|---|
| AutoCount | SME volume leader, dealer network | Desktop, Windows, local DB, one-time license | Highest-value import target (trading/retail/F&B) | Adoption = directional |
| SQL Account | Largest SME install base claim | Desktop, Windows, local DB | Second import target; trading/distribution focus | Adoption = directional |
| UBS Accounting | "Long-tail legacy", Sage-partnered | Very old desktop stack, dated tech | Cheapest-to-serve tail; lower fidelity expectations | Adoption = directional |
| Million | Long-standing local suite | Desktop, local DB | Long-tail | Adoption = directional |
| QNE / Mr. Accounting / others | Regional players | Desktop | Tail | Adoption = directional |

⚠️ **Do not assume their file formats.** Their export formats are *unknown* to us today; everything in §4.1 is marked **ASSUMPTION** until a real export sample is obtained.

### 1.2 Category B — Portal-era / batch-file government systems (legacy *systems* we integrate)

| External system | Legacy character | Integration mode | Deadline criticality |
|---|---|---|---|
| LHDN MyInvois (e-Invois) | **Not legacy** — modern REST SDK, OAuth2 client-credentials, 60-min tokens, SHA-256 `documentHash`, 300KB doc limit, UBL 2.1 JSON | API-first, facade over SDK | Legal filing window — highest stakes |
| MySST (Customs) | Portal + SST-02 return **file/portal** era | Portal/file → later API; ACL + manual assist fallback | Statutory return deadline |
| MyEG (EPF) | Portal + contribution schedule files | Portal/file + scheduled automation | Monthly statutory deadline |
| SOCSO / PERKESO | Portal, small employer schemes | Portal/file | Monthly |
| EIS (KWSP-managed) | Portal | Portal/file | Monthly |
| HRD Corp levy | Portal | Portal/file | Annual |
| LHDN MyTax (PCB/e-CP39) | Portal | Portal/file | Monthly/yearly |
| SSM / e-Info / MBRS (XBRL) | Portal + XBRL documents | Portal/file + XBRL generation | Annual return deadline |

**Key architectural consequence:** every Category-B system is a *legacy external system* in the strangler-fig sense — it will **not** get modernized on our timeline. Therefore **no domain module may depend on a portal-era system's data shape.** All access goes through an ACL facade that translates to canonical domain types.

### 1.3 Category C — Our own monolith risk (design-time)

Greenfield Next.js apps have a well-known failure mode: a single `app/` route tree becomes a monolith, and compliance logic (SST engine, e-Invois filing, payroll statutory) becomes entangled with UI. Preventive countermeasure: **modular monolith with enforced boundaries from day 1**, extracted to services only where scale/isolation requires it (§3).

---

## 2. Strategy Selection

| Situation | Pattern | Applied to |
|---|---|---|
| Legacy system we don't control, must integrate forever | **Strangler fig + ACL facade** | All Category-B systems |
| Legacy *data* format we must ingest once | **Anti-corruption adapter + canonical mapping** | Category-A desktop suite importers (W3) |
| Our own module we want to replace/extract later | **Branch by abstraction** | SST engine, filing gateway, payroll statutory |
| Changing external contract we can't control | **Facade + versioned adapter** | MyInvois SDK version drift |

**Branch-by-abstraction over big-bang rewrite** is the default for our own modules: the SST engine and the filing pipeline are compliance-critical — a big-bang replacement risks filing failures with legal consequence. We abstract behind a stable interface, migrate implementation behind it, and flip the switch per module.

---

## 3. Target Service / Module Boundaries

```
┌───────────────────────────────────────────────────────────────────────┐
│  Presentation (Next.js App Router)                                    │
│  SME workspace │ Firm multi-client workspace │ Compliance calendar   │
└───────────────┬───────────────────────────────────────────────────────┘
                │  (application-layer tenant context — non-negotiable)
┌───────────────▼───────────────────────────────────────────────────────┐
│  Domain Modules (modular monolith, single Postgres, strict schemas)   │
│                                                                       │
│  Ledger Core │ Tax Engine (SST) │ Payroll Statutory │                │
│  e-Invoice Orchestration │ Compliance Calendar │ AI Copilot (W2)     │
└───────┬───────────────────────────────────────────────┬───────────────┘
        │                                               │
┌───────▼────────────────────┐         ┌──────────────▼───────────────┐
│  FACADE LAYER (ACL)        │         │  MIGRATION IMPORT LAYER (W3)  │
│  FilingGateway             │         │  LegacySuiteAdapter          │
│  TaxFilingGateway          │         │   ├ AutoCountAdapter          │
│  PayrollGateway            │         │   ├ SqlAccountAdapter         │
│  CompanyRegistryGateway    │         │   ├ UbsAdapter                │
│  (all speak canonical      │         │   └ MillionAdapter            │
│   domain types)            │         │  ImportPipeline → canonical   │
└───────┬────────────────────┘         │  ledger entries (idempotent)  │
        │                              └───────────────────────────────┘
┌───────▼──────────────────────────────────────────────────────────────┐
│  Legacy External Systems (Category B)                                │
│  MyInvois SDK (API) │ MySST │ MyEG │ SOCSO │ EIS │ HRD │ MyTax │ SSM │
└──────────────────────────────────────────────────────────────────────┘
```

**Boundary rules (non-negotiable, proposed):**
1. **No module imports an SDK client directly.** Only facade/adapter code may talk to external systems.
2. **Facades return canonical domain types**, never vendor-shaped payloads, beyond the adapter boundary.
3. **Facade contracts are versioned internally** (`FilingGateway.v1`) so an external contract change is absorbed in one adapter, not N modules.
4. **Tenant context flows in the command, not as ambient state** — required for Firm Edition (W1) isolation correctness.
5. **Every facade call is audit-logged** with tenant, user, correlation id, external ref, and outcome (Restricted-class data access rule).
6. **Facade seams are defined by what an incumbent suite can express, not internal layout.** Do not add internal seams for symmetry.
7. **Seam contract (interface shape, error taxonomy, idempotency) is jointly owned** — Legacy Modernization Specialist proposes, Architecture Lead signs off before freeze.

---

## 4. Migration Playbooks

### 4.1 Playbook A — Legacy desktop suite import (W3, "Migration importers")

**Strangler position:** legacy suite = the *strangled* system. We do not replace it in place; we ingest a snapshot and progressively take over.

**Phased approach:**

| Phase | Mechanism | Risk |
|---|---|---|
| **A0 Discovery** | Obtain real export samples from each suite (customer-assisted + dealer-assisted) → record actual format spec | **BLOCKER: all format knowledge is currently ASSUMPTION** |
| **A1 Extract** | Customer uploads export file (CSV/XLSX/backup DB) to an intake bucket in ap-southeast-1 | File format variance, encoding (BM/ZH), delimiter/decimal quirks, huge row counts |
| **A2 Normalize** | Per-suite adapter → canonical staging schema; **quarantine unknown columns, never silently drop** | Data loss |
| **A3 Reconcile** | Opening balances + trial balance + key totals (AR, AP, inventory, tax) vs customer statement | Rounding, FX, opening-balance drift |
| **A4 Post** | Idempotent posting of opening balances into Ledger Core; import batches are reversible (soft-delete by batch id, never hard delete) | Double-posting, audit gap |
| **A5 Dual-run** | Parallel operation for one cycle; user signs off on reconciliation report | User fatigue |

**ASSUMPTION / TO-VERIFY (do not implement against these):** AutoCount/SQL Account/UBS/Million export file formats, whether they export a trial balance at all, chart-of-account structure, historical document retention.

**Hard constraints (non-negotiable, from Architecture Lead review):**
- **No importer against guessed format.** AutoCount/SQL/UBS assumptions until real samples obtained; every field carries a confidence label; unknowns quarantined, never dropped.
- **Canonical schema must treat unknown as first-class value** and confidence label as schema-enforced.
- Imported financial/personal data stays in **ap-southeast-1** (PDPA 2024) — no third-party parsing service outside the region.
- Imported data is **Restricted/Confidential class** → encrypted at rest, access-logged, tenant-scoped from the moment of upload.
- Imports must produce an **evidence-grade audit trail** (the competitive analysis calls out "compliance = shipping the form, not owning the workflow" — imports are the first trust moment).
- Import is **not** a bulk-insert fast path. It is a state machine with per-batch lineage.
- **Importer remains a module inside the monolith until L5** (extraction readiness), behind a clean port. No premature extraction.

### 4.2 Playbook B — Legacy external system integration (portal-era)

**Universal ACL pattern for portal-era systems (MySST, MyEG, SOCSO, EIS, HRD, MyTax, SSM):**

```
Domain Module → Gateway Facade → Adapter (portal/file) → Portal Automation / File Generator → Legacy System
                     ↑                    ↓
               canonical types    CompliancePolicy (schedule, format, deadline)
```

- **Portal automation is a last resort, not a default.** Prefer (1) published API if one exists → (2) bulk file generation + portal upload → (3) authenticated session automation, *only* where legally permitted and with explicit human-in-the-loop confirmation.
- **Human-in-the-loop is a feature, not a limitation.** Where a legacy portal cannot be automated safely, the product must model a **compliance work item** ("file ready, awaiting submission") with an owner, due date, and evidence link — the same model used for e-Invois. This is what turns a legacy-system constraint into a product moat.
- **Compliance work item materializes AI-advisory + human-approval constraint.** Keeps: owner, due, evidence + suggestion, source, decision, timestamp for audit evidence.
- **Credential handling:** portal credentials/tokens live in AWS Secrets Manager, never in env vars, never logged; every submission is actor-attributed (who in the firm filed on the client's behalf).

### 4.3 Playbook C — MyInvois / e-Invois filing path (highest stakes, already modern)

MyInvois is *not* legacy, but it is the most consequential integration and the one most likely to be reworked under deadline pressure. Treat it with the same discipline:

- **`FilingGateway` facade** wrapping the SDK: token lifecycle (60-min expiry) handled inside the adapter and **never surfaced upward**; SHA-256 `documentHash` generation in one place; 300KB document limit enforced with a clear user-facing error; duplicate-detection and cancellation rules owned by the adapter.
- **FilingGateway as anti-corruption layer over existing filing service** (ACCO-017/014/045) with its own idempotency-key namespace — **no second token cache**.
- **One interface, three operations:** `submit`, `status/query`, `reconcile-after-timeout` — exposing our reconcile-only posture (ACCO-045 D3).
- **Branch by abstraction for the document pipeline:** submit path behind `FilingGateway` so a future LHDN contract/version change, or a shift to intermediary (firm) submission, is absorbed in one adapter.
- **Idempotency key per document** so a retry after a network timeout cannot double-file (double-filing has statutory consequences).
- **Deadline-critical SLO separate from general app availability** (aligns with SRE goal G-MVIJTZV8-0001-KEBU).

---

## 5. Dependency Map (who depends on whom)

| Consumer | Depends on (facade) | External reality | Blocking risk |
|---|---|---|---|
| e-Invoice Orchestration | `FilingGateway` | MyInvois SDK (API) | Medium — contract drift, outage at filing window |
| Tax Engine | `TaxFilingGateway` | MySST portal/file | High — portal-only, no stable API |
| Payroll Statutory | `PayrollGateway` | MyEG / SOCSO / EIS / HRD / MyTax | High — 5 separate legacy systems, portal/file |
| Company/Entity master | `CompanyRegistryGateway` | SSM e-Info / MBRS XBRL | Medium — annual cycle only |
| Compliance Calendar | `CompliancePolicy` + all gateways | Regulatory calendars | Medium |
| Onboarding (W3) | `LegacySuiteAdapter` | None (customer-supplied files) | **High — format unknown (A0)** |
| AI Copilot (W2) | Ledger Core + Tax Engine only | — | Must **never** read raw SDK payloads (token/PII leakage) |

**Dependency rule:** facades depend on domain modules' canonical types; domain modules depend on facades. **No cycles.** Adapters depend on nothing but external SDKs/portals and their own canonical mapping.

---

## 6. Migration Roadmap (sequenced)

| Stage | Scope | Gate to proceed |
|---|---|---|
| **L0 Boundary contracts** | Define canonical types + facade interfaces (Filing, Tax, Payroll, Registry) and the `LegacySuiteAdapter` interface. No implementations. | CTO + Architecture Lead sign-off on interfaces |
| **L1 Vertical slice — filing** | `FilingGateway` + e-Invoice Orchestration end-to-end for one doc type (01) | Sandbox submission + status reconciliation working |
| **L2 Vertical slice — import** | One suite (highest value: AutoCount) + reconciliation report | Trial balance reconciles on 3 real customer datasets |
| **L3 Compliance work-item model** | Unified "awaiting submission / filed / rejected / overdue" work items across filing + payroll | Firm Edition visibility of per-client compliance state |
| **L4 Statutory adapters** | MySST → MyEG → SOCSO/EIS → HRD → MyTax, each behind its gateway | Each adapter meets deadline window in staging |
| **L5 Extraction readiness** | Extract modules to services where needed (filing is the first candidate: longest-running, most failure-prone I/O) | Measured need (queue depth, SLO breach), not anticipation |

Sequencing rationale: **L0 before everything** (interfaces are the cheap, high-leverage artifact); **filing before payroll** (one modern API teaches the pattern, then the legacy portals repeat it); **one suite importer before three** (format discovery dominates effort, and a second suite proves the adapter abstraction is real).

---

## 7. Proposed Mission (needs CTO approval to become lineage)

**Mission: M-Legacy — "Legacy Integration & Migration Boundaries"**
*Objective: establish the boundaries, facades, and migration roadmap that let the Malaysia Accounting SaaS integrate legacy external systems and ingest legacy desktop data without importing legacy complexity into the domain core.*

**Slice S1 — External Legacy Integration Boundaries**
- Feature F1: Canonical domain types + facade contracts for Filing / Tax / Payroll / Company Registry (acceptance: interfaces documented, reviewed by Architecture Lead, no vendor payloads cross the boundary). **Ownership: §7 F1 stays with Legacy Modernization Specialist; Architecture Lead signs off contract.**
- Feature F2: `FilingGateway` reference adapter over MyInvois SDK with token lifecycle encapsulated and idempotent submission (acceptance: sandbox submission works; reconciliation-after-timeout path tested; **anti-corruption layer over existing filing service with own idempotency-key namespace, no second token cache**).

**Slice S2 — Legacy Data Migration Boundaries (W3)**
- Feature F3: `LegacySuiteAdapter` interface + one concrete adapter (AutoCount) with canonical staging schema; unknown fields quarantined with confidence labels; unknown treated as first-class value in canonical schema; confidence label schema-enforced.
- Feature F4: Import pipeline (A0–A5) producing evidence-grade audit trail, idempotent posting, reversible batches; importer stays as module inside monolith until L5, behind clean port.

**Lineage status:** none until CTO approves M-Legacy; **open no tasks** until lineage exists.

---

## 8. Ownership Summary (per Architecture Lead review)

| Area | Owner | Sign-off |
|---|---|---|
| §7 Slice S1 / Feature F1 (canonical types + facade contracts) | Legacy Modernization Specialist | Architecture Lead |
| FilingGateway contract (interface, error taxonomy, idempotency) | Joint — Specialist proposes, Architecture Lead signs off | Architecture Lead |
| FilingGateway implementation (anti-corruption layer, token lifecycle, idempotency) | Legacy Modernization Specialist | — |
| Importer module (monolith until L5) | Legacy Modernization Specialist | — |
| Migration roadmap (L0–L5) | Legacy Modernization Specialist | CTO + Architecture Lead |

---

## 9. Next Steps

1. **Architecture Lead sign-off** on this v0.2 strategy document (facade contracts + FilingGateway anti-corruption layer + joint ownership rule + unknown-first-class + confidence schema enforced).
2. **CTO approval** of Mission M-Legacy to establish lineage for downstream tasks.
3. **No tasks opened** until lineage exists.

### 9.1 L0 deliverable (drafted 22 Oct 2026)

The L0 stage's concrete artifact is **`docs/legacy-facade-contracts.md`** (v0.1, artifact `9b684d36`) — the seam contract itself: canonical domain types, the four versioned gateway interfaces (`FilingGateway.v1`, `TaxFilingGateway.v1`, `PayrollGateway.v1`, `CompanyRegistryGateway.v1`), the `LegacySuiteAdapter` interface, one cross-gateway error taxonomy, idempotency semantics, audit hooks, dependency direction, named implementing modules, the gate A0 discovery protocol, and a decision log.

This document is the authoritative statement of *what the interfaces are*; this strategy document remains authoritative for *why the boundaries are where they are*. Where they disagree, the contracts document wins on interface shape and this document wins on strategy and sequencing.

Open items carried in the contracts document §11: interface type-binding discipline (TypeScript + Python), idempotency store placement, error→HTTP mapping ownership, `E_CAPABILITY_UNSUPPORTED` policy confirmation, and the `ComplianceWorkItem` state machine.

---

*This document is the single source of truth for legacy integration boundaries. All downstream implementation tasks must reference M-Legacy lineage once approved.*