---
title: Malaysia Accounting SaaS — Core Foundation Plan (Phase 1 SME-direct MVP)
doc-id: PLAN-CORE
baseline: v1
status: draft            # draft → in-review (2-day parallel) → frozen
author: Architecture Lead (drafted with Claude)
date: 2026-10-24
mission: M-⟨fill: Core Foundation mission code⟩   # "Malaysia Accounting SaaS Core Foundation" (exists in Fusion, 6 milestones)
slice: n/a (mission-level plan)
feature: n/a
compliance-regime: [LHDN MyInvois, ITA 1967, Companies Act 2016, Sales Tax Act 2018, Service Tax Act 2018, PDPA 2010 + Amendment 2024, Cyber Security Act 2024]
authoritative-sources:
  - LHDN e-Invoice General Guideline v4.8 (30 Aug 2026) + Specific Guideline
  - JPDP (PDP Commissioner) breach-notification, DPO, DPIA/ADMP/DPbD guidelines (DPIA/ADMP/DPbD issued 30 Apr 2026)
  - RMCD MySST guides (service tax 8%/6%, sales tax 5%/10%)
verification: facts checked 2026-10; re-verify monthly via the compliance fact table (D-DOCS-005)
---

# Core Foundation Plan — baseline v1

> **⚠ Before you commit this file:** replace each `⟨fill⟩` with the real M-/SL-/F- code shown in Fusion. The ACCO Cited-by lint fails while any placeholder remains. Two slices in §2 do not exist yet and are marked **NEW**: create them in Fusion first.

## 0. How to read and change this document

**Outline.** Section numbers are stable, because §1, §2 and §10 are cited externally. Design docs cite by **D-ID**, never by section number.

| § | Content | Kind |
|---|---|---|
| 0 | Conventions, lint rules, change rule | rules |
| 1 | Mission lineage | lineage |
| 2 | Module → slice map | lineage |
| 3 | D-SCOPE: in-scope, targets, exclusions | **definitions** |
| 4 | Entries by module, in ID order (decided, open, parked) | **definitions** |
| 5 | Open register | index |
| 6 | Parked register | index |
| 7 | Must-decide rule, pre-seeded must-decide lists, triage | rules + index |
| 8 | Owners: the bounded review slice per owner | index |
| 9 | Day-0 actions | actions |
| 10 | Fusion mission-page corrections (mirrored in Part B §B3) | lineage |
| 11 | Supersession table | index |

**Definition vs index.**
- Every entry is **defined exactly once**: as a heading or bold bullet in §3 or §4, or as a row of the §3 Exclusions table.
- §5, §6, §7.2 and §11 are index tables that only reference IDs.
- plan-lint fails on a second definition, or on an index row whose ID has no definition.

**Change rule.**
- **Before freeze:** corrections are plain edits.
- **After freeze:** the `baseline-v1` tag never moves.
- **Who may supersede:** only the **operator** may supersede an entry. Module owners may request a supersession but may not authorise it.
- **What a supersession is:** a PR, approved by the operator, that appends a new entry with `supersedes: D-X-NNN`. The old entry gets `superseded-by:` and status `superseded`. These are the only fields edited in place.
- **Reason and source:** each supersession states a reason and a new decision source. Valid sources:
  - an operator ruling recorded in the PR;
  - a design-doc decision the operator adopts, pinned to a commit SHA;
  - a fresh interview turn, **transcribed verbatim into the PR** so the record persists.
- **Closing an open entry** is a supersession under the same rule.
- **Index rows:** §11 gets a row for each supersession.
- **IDs.** Entries use `D-<MODULE>-NNN`, numbered from 001 within each module and never reused. Module codes become immutable at freeze.
- **Pre-freeze module additions.** v1 adds LEDGER, SALES, REPORTS, OPS and ONBOARD. Without them, five existing Fusion slices would have no module.
- **Statuses:**
  - `decided`
  - `open`: has an owner and a close-by.
  - `parked`: must cite the D-SCOPE exclusion it rests on.
  - `superseded`
- **CI lint (`plan-lint`) checks:**
  - ID format and uniqueness.
  - Every `parked` entry cites a D-SCOPE entry.
  - Every `open` entry has an owner and a close-by.
  - Every module maps to exactly one slice, and every Core slice has at least one module.
  - Every cited code exists.
  - Supersession links are two-way.
- **Review.** Two days, in parallel. Each module owner reviews their own module, and the CEO reviews D-SCOPE. A comment is either "edit" (pre-freeze correction) or "must-decide" (§7).

## 1. Mission lineage

| Mission | Role | Action |
|---|---|---|
| **Malaysia Accounting SaaS Core Foundation** (M-⟨fill⟩) | Single accountable mission and parent of D-SCOPE. 6 milestones: Platform & Core Infrastructure; Core Accounting & Compliance; E-Invoicing & Readiness; AI Capture & Banking; Migration & Reports; MVP Launch & Validation | None. This is the root |
| M-MVIJWNII-0005-29TQ Infrastructure foundation (K8s/IRSA, tenancy kernel, db-contracts) | **Overlaps.** Core's "Development Environment & CI/CD" and "Multi-tenant Kernel & Authentication" slices replace it for Phase 1, on Azure | Mark the overlapping slices `superseded-by` the Core slice. Keep their codes so existing Cited-by refs still resolve. db-contracts carries on only if Core cites it. Tracked in D-PLAT-010 |
| M-MVIJX5F9-000O-MY23 Audit log & firm beachhead | **Overlaps.** Core feature "Audit Events (G17)" owns Phase 1 audit | Audit-log slice: `superseded-by` Core G17 feature, or kept as the shared library Core depends on (D-AUDIT-003). Firm-beachhead slice: `parked`, citing D-SCOPE-018 |
| M-MVIJWODE-0007-QN4Z AI & LLM Foundation | **Constituent.** Supplies the eval harness and AI gateway, which Core does not contain | Add a depends-on link from Core "Document Capture" and "Bank Reconciliation" to its eval and gateway slices |

## 2. Module → slice map

| Module | Owner | Milestone | Slice (code) |
|---|---|---|---|
| SCOPE | CEO | — | mission root, M-⟨fill⟩ |
| PLAT | CTO | Platform & Core Infrastructure | Development Environment & CI/CD (SL-⟨fill⟩) |
| IDENT | Security/Platform Eng | Platform & Core Infrastructure | Multi-tenant Kernel & Authentication (SL-⟨fill⟩) |
| TENANCY | Architecture Lead | Platform & Core Infrastructure | Multi-tenant Kernel & Authentication |
| AUDIT | Architecture Lead | Platform & Core Infrastructure | Multi-tenant Kernel & Authentication (feature: Audit Events G17) |
| WORKSPACE | Product Manager | Platform & Core Infrastructure | Multi-tenant Kernel & Authentication (features: Membership Lifecycle, Role Permissions Matrix) |
| FCORE | Architecture Lead | Platform & Core Infrastructure | Filing-Core Library (SL-⟨fill⟩) |
| PRIV | DPO | Platform & Core Infrastructure | **NEW** slice: Privacy & Compliance Evidence |
| DOCS | DPO + Legal Counsel | Platform & Core Infrastructure | **NEW** slice: Privacy & Compliance Evidence |
| LEDGER | Tax Specialist | Core Accounting & Compliance | Ledger & Chart of Accounts (SL-⟨fill⟩) |
| SALES | Product Manager | Core Accounting & Compliance | Sales & Purchases (SL-⟨fill⟩) |
| SST | Tax Specialist | Core Accounting & Compliance | SST Tax Engine (SL-⟨fill⟩) |
| EINV | Integration Eng | E-Invoicing & Readiness | MyInvois Adapter (SL-⟨fill⟩) |
| COVER | Integration Eng | E-Invoicing & Readiness | MyInvois Adapter (**NEW** feature: Consolidation Coverage) |
| NOTES | Integration Eng + Tax Specialist | E-Invoicing & Readiness | MyInvois Adapter (**NEW** feature: Credit/Debit/Refund Notes) |
| READY | Product Manager | E-Invoicing & Readiness | Readiness View (SL-⟨fill⟩) |
| AUTOPILOT | Product Manager | E-Invoicing & Readiness | Readiness View (**NEW** feature: Compliance Calendar) |
| CAPTURE | AI Engineer | AI Capture & Banking | Document Capture (SL-⟨fill⟩) |
| BANK | Product Manager | AI Capture & Banking | Bank Reconciliation (SL-⟨fill⟩) |
| AUTO | Architecture Lead | AI Capture & Banking | Bank Reconciliation (**NEW** feature: Standing Approvals & Undo) |
| EVAL | Data Lead | (constituent) | M-MVIJWODE-0007-QN4Z eval-harness slice (SL-⟨fill⟩) |
| GW | AI Engineer | (constituent) | M-MVIJWODE-0007-QN4Z gateway slice (SL-⟨fill or create⟩) |
| IMPORT | Integration Eng | Migration & Reports | Data Migration (SL-⟨fill⟩) |
| REPORTS | Tax Specialist | Migration & Reports | Standard Reports (SL-⟨fill⟩) |
| OPS | CTO | MVP Launch & Validation | Go-Live & Monitoring (SL-⟨fill⟩) |
| ONBOARD | Product Manager | MVP Launch & Validation | User Onboarding & Feedback (SL-⟨fill⟩) |
| AIACCT | AI Engineer | — | none: parked (D-AIACCT-001) |

---

## 3. D-SCOPE (owner: CEO)

### D-SCOPE-001 — Positioning · decided
- **Market.** SME-direct accounting software for Malaysian businesses with **RM300k–RM25m turnover**.
- **Competition.** Head-on against QuickBooks, QNE, SQL Account and AutoCount.
- **Vision.** One intelligent hub, with compliance built into the core.
- **Later phases.** CRM/sales, payroll and further modules integrate later.
- **Accountants.** In Phase 1 they are collaborators invited into a client's business (D-WORKSPACE-001). The firm product comes later (D-SCOPE-018).
- **E-invoicing for exempt customers.** Many customers in the band are under RM3m, so they are exempt from e-invoicing unless they are related to an RM3m+ entity. For them the product offers e-invoicing as optional, and the readiness view shows them as N/A (D-READY-002).

### D-SCOPE-002 — Phase 1 MVP feature set · decided
The MVP is exactly the 6 milestones and their slices in the Core mission, plus the NEW slice and features in §2. Anything not on that list is out unless a new D-SCOPE entry adds it.

### D-SCOPE-003 — Definition of Done (Phase 1) · decided
A feature is done when all of the following hold:
- Its Fusion acceptance criteria pass in CI.
- Filing-type flows pass the filing-core conformance kit (D-FCORE-003).
- RLS tenancy tests pass.
- AI components have passed their EVAL release gate (D-EVAL-006).
- Audit events are emitted for state changes (D-AUDIT-001).
- BM/EN/ZH strings are complete.
- The DPO has signed off any new personal-data flow.
- Compliance artefacts the feature touches are activated by a fact-checked PR (D-DOCS-003).

### D-SCOPE-004 — Phase 1 targets · open (values proposed by the mission page)
- **Proposed values:**
  - MVP launch within 3 months.
  - Zero compliance defects.
  - Activation ≥40%.
- **Still needed:**
  - The CEO confirms the values.
  - A definition of **activation** (proposed: first approved e-invoice *or* first reconciled bank period within 14 days of sign-up).
  - A definition of **compliance defect** (proposed: any document LHDN rejects for a reason our validators should have caught, any wrong SST figure in an SST-02 draft, or any FILED status without a government reference).
- **Owner:** CEO. **Close-by:** end of review.

### D-SCOPE-005 — 3-month feasibility check · open
Six milestones, around 27 features, golden-set collection (≥240 documents, double-annotated) and the DPIA. If critical-path estimates exceed 12 weeks, re-plan. Owner: CEO, co-sign CTO. Close-by: end of sprint 0.

### D-SCOPE-024a — MyData access confirmed? · open
Decides whether D-SCOPE-024 (SSM lookup) is in scope or parked. Owner: CEO. Close-by: week 4.

### Exclusions (all decided; any entry that depends on one of these must be `parked` and cite it)
| ID | Excluded from Phase 1 |
|---|---|
| D-SCOPE-010 | **Payroll** (EPF/SOCSO/EIS/PCB). The mission description's "statutory payroll" must be removed (§10) |
| D-SCOPE-011 | WhatsApp / Telegram capture channels |
| D-SCOPE-012 | Native mobile apps. The PWA only |
| D-SCOPE-013 | Full inventory, costing and stock |
| D-SCOPE-014 | Multi-currency. MYR only |
| D-SCOPE-015 | Self-billed e-invoices |
| D-SCOPE-016 | Insight engine: tier-3 metrics, anomaly detection, tier-5, narrative |
| D-SCOPE-017 | Full "AI Accountant" and the in-app AI assistant |
| D-SCOPE-018 | Firm portfolio view and Tier 2 metrics, i.e. the firm plan |
| D-SCOPE-019 | CRM, marketplace and POS integrations |
| D-SCOPE-020 | Budgets, forecasting, collections automation (dunning sequences) |
| D-SCOPE-021 | Custom report builder |
| D-SCOPE-022 | Public/open API |
| D-SCOPE-023 | ISO 27001 / SOC 2 certification. Controls are built, certification is not pursued |
| D-SCOPE-024 | SSM company lookup. In scope only if MyData access is confirmed by week 4 |
| D-SCOPE-025 | **Direct bank feeds** and storing customers' bank credentials. Statement file import only |

---

## 4. Entries by module (decided, open and parked, in ID order within each module)

### PLAT (CTO)
- **D-PLAT-001 — Hosting region & network · decided.**
  - Azure Malaysia West.
  - Private Endpoints for all PaaS services.
  - NSG + Azure Firewall egress control.
  - No public data-plane endpoints.
- **D-PLAT-002 — Runtime · decided.** Azure Container Apps with Managed Identity. This replaces the K8s/IRSA scope of M-MVIJWNII-0005-29TQ for Phase 1.
- **D-PLAT-003 — Data & messaging · decided.**
  - PostgreSQL Flexible Server.
  - Service Bus.
  - Blob Storage, with immutable (WORM) containers for statutory evidence.
  - Key Vault for secrets, certificates and signing material.
- **D-PLAT-004 — Backend · decided.** Python 3.11, FastAPI, Pydantic v2.
- **D-PLAT-005 — Frontend · decided.**
  - React + TypeScript SPA (Vite) as a PWA.
  - Tailwind + shadcn/ui.
  - TanStack Query.
  - i18next (BM/EN/ZH).
  - MSAL.js.
  - Strict CSP.
- **D-PLAT-006 — Delivery · decided.**
  - Terraform for all infrastructure.
  - GitHub Actions for CI/CD.
  - CI runs lint, tests (including frontend `npm run lint` and `vitest run`), security scans and the route coverage guard.
  - Deploys include migrations and rollback.
  - Production refuses mock mode (G14).
- **D-PLAT-010 — Re-scope the older infra mission's slices · open.** Close or retarget the K8s/IRSA and tenancy-kernel slices in M-MVIJWNII-0005-29TQ, and decide whether db-contracts carries on. Owner: CTO, co-sign Architecture Lead. Close-by: sprint 0.

### IDENT (Security/Platform Eng)
- **D-IDENT-001 — Identity provider · decided.**
  - Entra External ID with OIDC auth-code + PKCE via MSAL.js.
  - Signing keys are cached and rotate automatically.
  - Only RS256 is accepted.
  - iss/aud/exp/nbf are checked with a small clock skew.
  - Users are keyed on `oid`/`sub`, never email.
  - Unauthenticated requests get a 401 with a `WWW-Authenticate` header.
- **D-IDENT-002 — MFA · decided.**
  - Enforced by Conditional Access.
  - Email OTP is the baseline method. Passkeys are available once the custom domain is live. SMS is for recovery only.
  - The API checks `'mfa' in claims.get('amr', [])` only when `MFA_CLAIM_ENFORCED=true`. The flag stays off until the spike confirms the claim is present.
  - Failures return a generic 401.
- **D-IDENT-003 — Token handling · decided.** Tokens are kept in memory only.
- **D-IDENT-004 — Abuse protection · decided.**
  - Repeated 401s and 403s are rate-limited.
  - Error messages are generic, so there is no account enumeration.

### TENANCY (Architecture Lead)
- **D-TENANCY-001 — Tenant context · decided.**
  - The client sends an `X-Business-Id` header, validated against `business_membership`.
  - Each request runs in one transaction: `SET LOCAL app.business_id`, then all queries, then commit.
  - The app's database role cannot bypass RLS.
  - A query with no context returns zero rows.
  - Safe with connection pooling.
- **D-TENANCY-002 — Route coverage guard · decided.**
  - Two allow-lists:
    - public: health check, OIDC callback.
    - authenticated-no-tenant: `/me`, `/me/businesses`, `/invites/accept`, `POST /businesses`.
  - Every other route requires membership.
  - A CI test fails if any route is uncovered.
- **D-TENANCY-003 — Roles · decided.**
  - Roles are a full table: owner, admin, staff, external accountant.
  - The matrix covers 10 actions:
    - view books
    - upload receipts
    - approve AI drafts
    - submit e-invoices
    - prepare SST
    - manage members
    - manage billing
    - manage MyInvois intermediary authorisation
    - export data
    - manage settings
  - It is enforced on every route.

### WORKSPACE (Product Manager)
- **D-WORKSPACE-001 — Accountant access · decided.**
  - The owner must approve the invite.
  - The external accountant can approve and close.
  - They cannot manage members, billing or settings.
  - No portfolio view (D-SCOPE-018).
- **D-WORKSPACE-002 — Membership lifecycle · decided.**
  - Invites carry a single-use token that expires in 7 days and is matched to the signed-in `oid`.
  - Removal and role changes take effect on the next request.
  - The last owner cannot be removed.
  - Ownership transfer needs a two-step confirmation.
  - Users can leave a business themselves.

### AUDIT (Architecture Lead)
- **D-AUDIT-001 — Audit events · decided.**
  - Append-only and tenant-scoped, per filing-core G17.
  - Covers sign-in, failed sign-in, MFA, invites, membership changes, business creation, and every action class in D-AUTO-001.
  - No tokens in logs.
  - Background jobs record the actor as `system:<job>`.
- **D-AUDIT-002 — Retention · decided.** Seven years (ITA 1967 / Companies Act 2016), with evidence packages in WORM storage.
- **D-AUDIT-003 — Older audit-log slice · open.** The audit-log slice in M-MVIJX5F9-000O-MY23 is either superseded by Core G17 or kept as a shared library Core depends on. Owner: Architecture Lead. Close-by: sprint 0.

### PRIV (DPO)
- **D-PRIV-001 — Roles under PDPA · decided.** We are a processor for customers' books and a controller for our own users and leads. A human DPO is appointed and JPDP is notified within 21 days.
- **D-PRIV-002 — Breach handling · decided.** Commissioner within 72h. Affected individuals within 7 days of that notice where significant harm is likely. The runbook is linked from OPS.
- **D-PRIV-003 — DPIA required · decided.** AI categorisation and extraction count as automated decision-making under the 30 Apr 2026 guideline, so a DPIA is mandatory before pilot. AI is never the sole decider.
- **D-PRIV-004 — Residency & training · decided.**
  - Data and AI processing stay in Malaysia West, or in Azure regional **Standard** deployments that `tenant_ai_residency` permits. Never Global.
  - No training on customer data without opt-in.
- **D-PRIV-005 — AI data-path spike: decision matrix · decided.**
  - Regional Standard deployment OK → proceed.
  - Modified abuse monitoring denied → take the fallback set in the matrix.
  - Capacity unavailable → Document Intelligence-only extraction plus abstention.
  - The spike's actual outcome is D-PRIV-006.
- **D-PRIV-006 — AI data-path spike outcome · open.** Applied via the D-PRIV-005 matrix. Owner: CTO, co-sign DPO + Data Lead. Close-by: spike day 2.

### FCORE (Architecture Lead)
- **D-FCORE-001 — filing-core v1.0 · decided.**
  - Guarantees G1–G20.
  - Pydantic models cover every filing type, and Protocols define the adapter methods.
  - Seeded from ACCO-054, the MyInvois client.
- **D-FCORE-002 — Freeze · decided.** Frozen in sprint 0. Changes after freeze go through a supersession entry approved by the Architecture Lead.
- **D-FCORE-003 — Mock/real gate & lifecycle · decided.**
  - `MOCK-` references are rejected in production.
  - `FILED` requires a government reference.
  - Every filing adapter passes the conformance kit.
  - An adapter is promoted to Live only after the soak gate and a signed acceptance ticket.
- **Pre-seeded must-decide list:** none.

### LEDGER (Tax Specialist)
- **D-LEDGER-001 — Chart of accounts · decided.** An MPERS-oriented chart with Malaysian statutory accounts. Customisable; seeded by migration. MYR only.
- **D-LEDGER-002 — Journals · decided.**
  - Double-entry, and entries must balance.
  - Posted entries are immutable; corrections are reversals.
  - Every change has an audit trail.
  - Bulk import supported.
  - Posting is a `post_ledger`-class action, which never runs under a standing approval (D-AUTO-002).

### SALES (Product Manager)
- **D-SALES-001 — Sales flow · decided.**
  - Quotation → invoice → payment.
  - SST lines are applied from the SST engine.
  - E-invoices are issued through EINV, including consolidated B2C.
- **D-SALES-002 — Bills & expenses · decided.**
  - Bills come from file upload or email-in.
  - AI suggests the category and tax code, citing its source. The user approves.
  - Duplicate checks run on every bill.
  - Received e-invoices can be matched to bills (D-EINV-007).
- **D-SALES-003 — Meaning of "payment reminders" · open.** A user-triggered or single scheduled reminder is in scope; dunning sequences are parked under D-SCOPE-020. Owner: Product Manager. Close-by: review window.

### SST (Tax Specialist)
- **D-SST-001 — Engine · decided.**
  - Service tax 8% and 6%; sales tax 5% and 10%; registration threshold RM500k.
  - Rates and thresholds live in the fact table.
  - Administered by RMCD via MySST, not LHDN.
  - The Tax Specialist signs off the rules.
- **D-SST-002 — Tax codes · decided.**
  - The codes follow the SST regime and the MyInvois tax-type code list: sales tax, service tax, tourism tax, high-value goods tax, low value goods tax, not applicable, exempt.
  - **Not the GST-era codes** (SR/ZR/ZS etc.). GST was repealed in 2018.
  - The internal code set maps 1:1 to MyInvois tax types.
- **D-SST-003 — Output · decided.**
  - An SST-02 draft, which must match hand-calculated test data.
  - Blockers are listed and feed READY.
  - Filing in MySST is a `file`-class action done by a human.

### EINV (Integration Eng)
- **D-EINV-001 — Submission · decided.**
  - Transactional outbox, then async MyInvois submission with status polling.
  - Invalid documents come back with clear errors.
  - UIN, long ID and QR are stored on validation.
  - Cancellation only inside the 72h window.
  - Intermediary authorisation is supported.
  - Certificates are held in Key Vault, and jobs authenticate as system actors.
- **D-EINV-002 — Consolidated B2C · decided.**
  - Summary lines are partitioned by business × month × series, with a 250 KB guard.
  - A single transaction over RM10,000 is never consolidated.
- **D-EINV-003 — Number space · decided.**
  - A `receipt_number_claim` ledger with an int8range exclusion constraint.
  - A gapless counter is assigned at issue. Counter rows are transactional, so a rollback leaves no gap.
- **D-EINV-004 — Issued vs e-invoiced boundary · decided.** "Issued" is internal. "E-invoiced" requires an LHDN validation reference.
- **D-EINV-005 — Remediation · decided.** Fixes are prepared by the system and approved by a human.
- **D-EINV-006 — Applicability · decided.**
  - Guideline v4.8: businesses under RM3m are exempt unless related to an RM3m+ entity.
  - Phase 4 (RM3m–5m) runs from 1 Jan 2026, with relaxation to 31 Dec 2027.
  - These rules are kept in the fact table.
- **D-EINV-007 — Received documents inbox · decided.**
  - E-invoices issued to the business by suppliers are pulled from MyInvois into an inbox.
  - The user is notified and can match them to bills.
  - The rejection window is handled per the guideline.
- **D-EINV-010 — `line_kind` wording vs the LHDN field definitions · open.** Owner: Tax Specialist, co-sign Integration Eng. Close-by: before the e-Invoicing design doc freezes.
- **D-EINV-011 — Late sale after the month's consolidation was submitted · open.** Owner: Tax Specialist. Close-by: before the e-Invoicing design doc freezes.
- **D-EINV-012 — Buyer asks for an individual e-invoice after consolidation · open.** Owner: Tax Specialist, co-sign Integration Eng. Close-by: before the e-Invoicing design doc freezes.
- **D-EINV-013 — Permitted summary forms; multiple consolidated documents per month per series · open.** Owner: Tax Specialist. Close-by: before the e-Invoicing design doc freezes.

### COVER (Integration Eng)
- **D-COVER-001 — Coverage invariant · decided.**
  - Each receipt is covered exactly once, by an individual e-invoice or by one consolidated line.
  - Stored as `coverage_claim`.
- **D-COVER-002 — Atomic groups · decided.** Groups come from a dependency graph. Validation enumerates the dependency-closed sets per segment.
- **D-COVER-003 — Fix-all · decided.** All-or-nothing: if any member fails, nothing is applied.

### NOTES (Integration Eng + Tax Specialist)
- **D-NOTES-001 — Generation · decided.** Credit, debit and refund notes are generated from the canonical UBL of the original document.
- **D-NOTES-002 — Credit ledger · decided.**
  - Movements: SEED / RESERVE / CONFIRM / RELEASE / REVERSE.
  - `CHECK (available >= 0)`.
- **D-NOTES-003 — Line kinds · decided.** `receipt_reversal` vs `value_adjustment`. Value adjustments carry a `value_check` artefact.
- **D-NOTES-004 — Hashes & retention · decided.**
  - The content hash and the evidence hash are kept separate.
  - Canonical packages are stored in WORM for the statutory period.

### READY (Product Manager)
- **D-READY-001 — Rules · decided.**
  - Deterministic.
  - Each rule has a severity, `blocker` or `risk`, and a deadline ladder.
  - Each rule cites its statutory source.
  - Built on the FCORE G19 framework, with tests for every rule.
- **D-READY-002 — States · decided.**
  - Red = blocker.
  - Amber = risk.
  - Green = ready.
  - **Grey = N/A**, which is a declared applicability record with a reason. It is auto-downgraded if conflicting evidence turns up.
  - The Fusion "Traffic Light Dashboard" acceptance must include grey (§10).
- **D-READY-003 — Rollup · decided.**
  - Per business, nearest deadline first.
  - Click-through to resolve.
  - Live update.

### AUTOPILOT (Product Manager)
- **D-AUTOPILOT-001 — Behaviour · decided.**
  - Builds a compliance calendar per business from the fact table.
  - Prepares actions but never runs `file` or `submit` actions.

### CAPTURE (AI Engineer)
- **D-CAPTURE-001 — Pipeline · decided.**
  - Step 1: if a MyInvois QR is present, take the shortcut.
  - Step 2: otherwise Document Intelligence plus Azure OpenAI vision (Standard regional only).
  - Step 3: deterministic validators.
  - Below confidence, the pipeline abstains. The image is always attached to the entry.
- **D-CAPTURE-002 — Channels · decided.**
  - PWA camera, web upload, email-in.
  - Chat channels are out (D-SCOPE-011).
- **D-CAPTURE-003 — Two separate metrics · decided.**
  - *Correctness gate:* D-EVAL-002, i.e. ≥98% precision with abstention.
  - *Automation KPI:* the share of captures approved without edits, target ≥70%.
  - The Fusion acceptance currently conflates them (§10).

### EVAL (Data Lead)
- **D-EVAL-001 — Golden set · decided.**
  - Six cells: 3 tiers × Latin/Chinese, at least 40 documents per cell.
  - Splits: locked 300, dev 150, QR 30.
- **D-EVAL-002 — Bar · decided.**
  - Precision ≥98% on total, SST and date, with abstention allowed.
  - Wilson lower bound ≥95% per tier.
- **D-EVAL-003 — Masking · decided.** Protect → mask → verify, using pixel hashes.
- **D-EVAL-004 — Annotation · decided.** Double annotation with an adjudicator.
- **D-EVAL-005 — Leakage & synthetic data · decided.** The six-part leakage control applies. Synthetic data is descriptor-based.
- **D-EVAL-006 — Release · decided.**
  - The Data Lead signs, with co-signs.
  - Staged rollout.
  - Degradation is handled per tenant.

### GW (AI Engineer)
- **D-GW-001 — Gateway · decided.**
  - In-house and Azure-only.
  - The versioned routing table is baked into the image.
  - The `tenant_ai_residency` constraint is enforced.
- **D-GW-002 — Change control · decided.**
  - Classes R, M and Q, with notice campaigns.
  - A dry-run authorize probe runs on a zero-traffic revision before promotion.

### BANK (Product Manager)
- **D-BANK-001 — Import · decided.**
  - Statement file import only (CSV/OFX/PDF formats per bank), MYR only.
  - No stored bank credentials (D-SCOPE-025).
- **D-BANK-002 — Categorisation & matching · decided.**
  - Suggestions are explainable and pass through the eval harness.
  - Duplicate-safe matching.
  - Applying a suggestion happens only under the D-AUTO rules.

### AUTO (Architecture Lead)
- **D-AUTO-001 — Action classes · decided.** read / draft / apply_internal / post_ledger / file / submit / external_send.
- **D-AUTO-002 — Standing approvals · decided.** Only for `apply_internal` and bank categorisation, under memory rules.
- **D-AUTO-003 — Predicate · decided.** Exact `payee_key ∈ approved_payee_set` AND direction AND amount band.
- **D-AUTO-004 — Payee keys · decided.** Typed keys (biller, counterparty, name). Membership is an OR across key types, with a conflict guard.
- **D-AUTO-005 — Alias approval · decided.** Goes through the standing-approval authority, with either retro-confirm or probation.
- **D-AUTO-006 — Undo · decided.** Every undo records its reason, and the reason is attributed.
- **D-AUTO-007 — Soft review · decided.**
  - Only an explicit resume ends it, and context carries over fully.
  - Acknowledgements are period-scoped with a review-by date.
  - On the third acknowledgement it becomes a hard block offering Resume, Edit or Revoke.
  - Escalation is a soft nudge, not a lock.
- **D-AUTO-008 — Evidence screen · decided.** Tiered evidence screen shown before approval.

### IMPORT (Integration Eng)
- **D-IMPORT-001 — First importer · decided.**
  - QNE import plus CSV/Excel templates.
  - All data types are mapped, validation errors are reported, and the trial balance must match after import.
- **D-IMPORT-002 — Native importers after QNE · open.** SQL Account + AutoCount (Fusion) vs QuickBooks (positioning). Recommendation: SQL Account and AutoCount native, QuickBooks via the CSV template. Owner: CEO, co-sign Product Manager. Close-by: sprint 1.
- **D-IMPORT-003 — History depth on import · open.** Opening balances only, or N months of transactions. Owner: Product Manager, co-sign Tax Specialist. Close-by: sprint 1.

### REPORTS (Tax Specialist)
- **D-REPORTS-001 — Standard set · decided.**
  - P&L (with comparison periods), balance sheet (A = L + E), trial balance, AR/AP aging (current/30/60/90+), SST summary (must match the SST-02 draft).
  - **General ledger / account detail report.** It is missing from Fusion and needs adding (§10).
  - PDF and Excel export.

### OPS (CTO)
- **D-OPS-001 — Observability · decided.** OpenTelemetry metrics, logs and traces go to Azure Monitor. Alerts are configured.
- **D-OPS-002 — Readiness to go live · decided.**
  - A restore from backup has been tested.
  - The incident runbook includes the PDPA breach path (D-PRIV-002).
  - Email support, published docs and a status page are live.

### ONBOARD (Product Manager)
- **D-ONBOARD-001 — Self-serve onboarding · decided.**
  - Steps: company setup → MyInvois intermediary authorisation (or a declared N/A) → first transaction.
  - Completion rate is measured, with help at every step, in BM/EN/ZH.
- **D-ONBOARD-002 — Feedback · decided.** In-app feedback and surveys, collected on a dashboard.

### DOCS (DPO + Legal Counsel)
- **D-DOCS-001 — Artefact sets · decided.**
  - Sets A, B, B-split and C, generated from the fact table.
  - Stored at `docs/compliance/artefacts/<set>/v<N>/`.
- **D-DOCS-002 — Pre-approval · decided.** The DPO pre-approves each artefact set before its activation PR.
- **D-DOCS-003 — Activation · decided.** Each activation PR runs a CI fact-check against a signed probe report generated by machine.
- **D-DOCS-004 — Probe · decided.**
  - Each row reports `ok`, `absent` or `error`.
  - Fail-closed: an `error` row blocks activation.
- **D-DOCS-005 — Fact table · decided.** Residency-critical fields are api-only, never hand-entered. This is the single source for rates, thresholds and deadlines.
- **D-DOCS-006 — Evidence · decided.**
  - Reports go to a WORM evidence store, with an index in the repo.
  - An offline verifier, export bundles approved by the DPO, and a replicated archive.

### AIACCT (AI Engineer)
- **D-AIACCT-001 — In-app assistant · parked** (D-SCOPE-017). The Core mission has no slice for it, and the 3-month target can't carry it.

---

## 5. Open register (index; definitions are in §3/§4)

| ID | Question | Owner | Co-sign | Close-by | Ticket |
|---|---|---|---|---|---|
| D-SCOPE-004 | Targets, plus definitions of activation and compliance defect | CEO | — | End of review | ACCO-0⟨fill⟩ |
| D-PRIV-006 | AI data-path spike **outcome**, applied via the D-PRIV-005 matrix | CTO | DPO, Data Lead | Spike day 2 | ACCO-0⟨fill⟩ |
| D-PLAT-010 | Close or retarget the K8s/IRSA and tenancy-kernel slices in M-MVIJWNII-0005-29TQ. Does db-contracts carry on? | CTO | Architecture Lead | Sprint 0 | ACCO-0⟨fill⟩ |
| D-AUDIT-003 | Audit-log slice in M-MVIJX5F9: superseded by Core G17, or kept as a shared library Core depends on? | Architecture Lead | — | Sprint 0 | ACCO-0⟨fill⟩ |
| D-IMPORT-002 | Native importers after QNE: **SQL Account + AutoCount** (Fusion) vs **QuickBooks** (positioning). Recommendation: SQL Account and AutoCount native in Phase 1, QuickBooks via the CSV template | CEO | Product Manager | Sprint 1 | ACCO-0⟨fill⟩ |
| D-IMPORT-003 | History depth on import (opening balances only, or N months of transactions) | Product Manager | Tax Specialist | Sprint 1 | ACCO-0⟨fill⟩ |
| D-SALES-003 | Meaning of "payment reminders": a user-triggered or single scheduled reminder, which is in scope, vs dunning sequences, which are parked under D-SCOPE-020 | Product Manager | — | Sprint 1 | ACCO-0⟨fill⟩ |
| D-EINV-010 | `line_kind` wording on notes vs the LHDN field definitions | Tax Specialist | Integration Eng | Before EINV freeze | ACCO-0⟨fill⟩ |
| D-EINV-011 | Late-sales rule: a sale recorded after its month's consolidation was submitted | Tax Specialist | — | Before EINV freeze | ACCO-0⟨fill⟩ |
| D-EINV-012 | A buyer asks for an individual e-invoice after the sale was consolidated | Tax Specialist | Integration Eng | Before EINV freeze | ACCO-0⟨fill⟩ |
| D-EINV-013 | Permitted summary forms, and whether multiple consolidated documents per month per series are allowed | Tax Specialist | — | Before EINV freeze | ACCO-0⟨fill⟩ |
| D-SCOPE-024a | MyData access confirmed? (decides between in-scope and parked) | CEO | — | Week 4 | ACCO-0⟨fill⟩ |
| D-SCOPE-005 | 3-month feasibility check: 6 milestones, around 27 features, plus golden-set collection (≥240 documents, double-annotated) and the DPIA. Re-plan if critical-path estimates exceed 12 weeks | CEO | CTO | End of sprint 0 | ACCO-0⟨fill⟩ |

## 6. Parked register (index)

| ID / item | Rests on | Revisit at |
|---|---|---|
| D-AIACCT-001 | D-SCOPE-017 | Phase 2 planning |
| Firm-beachhead slice, M-MVIJX5F9-000O-MY23 (board item, not a D-entry) | D-SCOPE-018 | Phase 2 Firm plan |

Any entry raised in review that touches a §3 exclusion is filed as `parked` and cites that exclusion.

## 7. Must-decide rule, pre-seeded lists, triage

### 7.1 Rule
An item is **must-decide before the freeze of the document it gates** if it meets any of these five criteria. For plan.md entries the gated document is plan.md itself, unless §7.2 names a design doc.

The five criteria:
1. It is a statutory or regulatory interpretation.
2. It is irreversible once data exists: schema, numbering, retention.
3. It is a contract between modules or squads.
4. It touches residency or personal data.
5. It is an external commitment: a customer, LHDN or RMCD.

Everything else may stay `open` past freeze, with an owner and a close-by.

> **Verify:** check these five criteria against the wording agreed in the interview record.

### 7.2 Pre-seeded must-decide lists (index)

| Gated document | Items that must close before it freezes | Criterion |
|---|---|---|
| filing-core design doc (FCORE v1.0) | **none** | — |
| e-Invoicing design doc | D-EINV-010, D-EINV-011, D-EINV-012, D-EINV-013 | 1 (statutory) |
| e-Invoicing design doc | D-AUDIT-003 (G17 audit target for issuance events) | 3 (contract) |
| plan.md baseline v1 itself | D-SCOPE-004, D-SCOPE-005, D-PRIV-006 | 5, 5, 4 |
| SST design doc | none pre-seeded. The Tax Specialist adds items at review | — |

Items in §5 that are not listed here (D-PLAT-010, D-IMPORT-002/003, D-SALES-003, D-SCOPE-024a) may stay open past freeze with their close-by.

### 7.3 Triage
- Module owners triage comments raised in their own module.
- The CEO triages anything that touches D-SCOPE.
- Ties go to the Architecture Lead.

## 8. Owners

| Role | Owns |
|---|---|
| CEO | SCOPE |
| CTO | PLAT, OPS, PRIV spike outcome |
| Architecture Lead | FCORE, TENANCY, AUDIT, AUTO, freeze |
| DPO | PRIV, DOCS approvals |
| Data Lead | EVAL |
| Tax Specialist | LEDGER, SST, REPORTS, the statutory EINV/NOTES items |
| Security/Platform Eng | IDENT |
| Integration Eng | EINV, COVER, NOTES, IMPORT |
| AI Engineer | CAPTURE, GW |
| Product Manager | SALES, READY, AUTOPILOT, BANK, WORKSPACE, ONBOARD |

## 9. Day-0 actions (humans, not agents)

0. Make the §10 edits in Fusion, create the NEW slice and features, then replace every `⟨fill⟩` in this file.
1. File the Azure OpenAI quota request and the modified-abuse-monitoring request. *These requests start the clock for D-PRIV-006.*
2. DPO pre-approves artefact sets A, B, B-split and C, and opens the DPIA.
3. Tax Specialist starts D-EINV-010 to 013 and the D-SST-002 code mapping.
4. Keep Fusion **Autopilot off** until this plan is frozen, so no slice gets planned against unfrozen decisions. Then start the 2-day review and freeze.

## 10. Fusion mission-page corrections

| Where | Change |
|---|---|
| Mission description | Remove "statutory payroll" (D-SCOPE-010) |
| SST Tax Codes | Replace "ZR, SR, ZS, etc." with the SST/MyInvois tax types (D-SST-002) |
| Web & Camera Capture | Split the acceptance into a correctness gate (D-EVAL-002) and an automation KPI of ≥70% approved without edits (D-CAPTURE-003) |
| Bank Import | Remove "direct bank feed" and "secure credentials stored". Statement files only (D-SCOPE-025) |
| Traffic Light Dashboard | Add grey (declared N/A) and the deadline-first sort (D-READY-002/003) |
| Quotations & Invoices | Clarify what "payment reminders" means (D-SALES-003) |
| Standard Reports | Add a General Ledger feature |
| MyInvois Adapter | Add features: Consolidation Coverage, Credit/Debit/Refund Notes |
| Readiness View | Add feature: Compliance Calendar |
| Bank Reconciliation | Add feature: Standing Approvals & Undo |
| Platform & Core Infrastructure | Add slice: Privacy & Compliance Evidence (DPIA, breach runbook, artefact sets, fact table, probe) |
| Document Capture, Bank Reconciliation | Add depends-on links to the eval-harness and gateway slices in M-MVIJWODE-0007-QN4Z |

## 11. Supersession table (index)

| New entry | Supersedes | Reason | Decision source (operator ruling / adopted design doc @SHA / transcribed interview turn) | Approved by operator (PR) |
|---|---|---|---|---|
| _none at baseline v1_ | | | | |
