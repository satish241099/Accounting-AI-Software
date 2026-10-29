---
title: Core Foundation Mission — board snapshot (Part A) + intended delta (Part B)
doc-id: MISSION-CORE
status: draft
mission: M-⟨from Part A⟩   # "Malaysia Accounting SaaS Core Foundation"
part-a-author: workflow-planner agent (live board read; unedited)
part-b-author: assistant draft → signed by the owning module lead per item (see Owner column)
date: 2026-10-24
---

# Part A — As-is snapshot (planner agent; DO NOT HAND-EDIT)

> To be generated from a live board read.
> Required fields: read timestamp, read hash, mission code and status, 6 milestones, all slices, all features, and every code.
> If the read disagrees with Part B's assumptions, the planner **stops and reports**. It does not correct Part A to fit.

_⟨pending planner read⟩_

---

# Part B — Intended delta (names only, no codes)

## Conventions

- Every acceptance clause cites the D-entry it comes from.
- A clause that no decided entry backs is tagged **[OWNER-DECISION]**. The named owner must sign it, and it becomes a new D-entry in plan.md in the same PR.
- A clause that depends on an open entry is tagged **[PENDING D-x]**. It cannot freeze until that entry closes.
- Each "Before" text was taken verbatim from the mission page pasted on 2026-10-24. Reconciliation must confirm it against Part A, and **any mismatch blocks** the PR.
- The new-code count is **"exactly the items in B1 + B2"**, not a hard-coded number. If B2 is approved as drafted, that is 1 slice + 9 features = **10 codes**.

## B0. Clause-resolution table (re-derived 2026-10-24 against plan.md v1)

| Clause / topic | Where in Part B | Status | Cites |
|---|---|---|---|
| Consolidated payload size: 250 KB guard / split | B1-1 | settled, cited | D-EINV-002 |
| Coverage partition: business × month × series | B1-1 | settled, cited | D-EINV-002 |
| No consolidation of a single transaction >RM10,000 | B1-1 | settled, cited | D-EINV-002 |
| Receipt-number-space ledger, gapless counter at issue | (EINV; not a B1 clause) | settled, cited | D-EINV-003 |
| Exactly-once coverage, atomic groups, Fix-all | B1-1 | settled, cited | D-COVER-001/002/003 |
| Credit ledger, line kinds (mechanics), hashes, WORM | B1-2 | settled, cited | D-NOTES-001..004 |
| **Late sale recorded after the month's consolidation was submitted** | B1-1 | **still pending**: statutory, Tax Specialist | D-EINV-011 |
| **Buyer asks for an individual e-invoice after the sale was consolidated** | B1-1 | **still pending**: statutory, Tax Specialist | D-EINV-012 |
| **`line_kind` wording vs the LHDN field definitions** | B1-2 | **still pending**: statutory, Tax Specialist | D-EINV-010 |
| Permitted summary forms / multiple consolidated docs per month | not cited in Part B | still pending; no marker needed | D-EINV-013 |
| Meaning of "payment reminders" | B3-C8 | still pending; product call by the Product Manager, close in review window | D-SALES-003 |
| Audit-log slice: superseded vs shared library | B4-L3 (a link, mints no code) | still pending; Architecture Lead, sprint 0 | D-AUDIT-003 |

Rules:
- A clause whose substance is a decided plan.md entry is a normal cited clause. It is never marked pending.
- If a decision exists only in the interview record and not yet in plan.md, record it as a decided plan.md entry in the same PR, then cite it.
- The owner confirms only the rows that are still pending. Settled rows need no re-confirmation.
- This table is frozen with Part B.

## B1. New features under existing slices (5)

| # | Feature (name) | Parent slice | Owner (signs) |
|---|---|---|---|
| 1 | Consolidation Coverage | MyInvois Adapter | Integration Eng |
| 2 | Credit/Debit/Refund Notes | MyInvois Adapter | Integration Eng + Tax Specialist |
| 3 | Compliance Calendar | Readiness View | Product Manager |
| 4 | Standing Approvals & Undo | Bank Reconciliation | Architecture Lead |
| 5 | General Ledger | Standard Reports | Tax Specialist |

**1. Consolidation Coverage.** Description: guarantees every receipt is reported to LHDN exactly once, either individually or in a consolidated B2C document.
Acceptance:
- Each receipt is covered exactly once, by an individual e-invoice or one consolidated summary line, enforced by `coverage_claim` (D-COVER-001).
- Summary lines are partitioned by business × month × series, with a 250 KB payload guard.
- Any single transaction above RM10,000 is excluded from consolidation and routed to individual issuance (D-EINV-002).
- Atomic groups are derived from the dependency graph and validated by enumerating dependency-closed sets per segment (D-COVER-002).
- Fix-all is all-or-nothing (D-COVER-003).
- Remediation is prepared by the system and approved by a human (D-EINV-005).
- Late sales after submission of the month's consolidation are handled per **[PENDING D-EINV-011]**.
- A buyer request for an individual e-invoice after consolidation is handled per **[PENDING D-EINV-012]**.

**2. Credit/Debit/Refund Notes.** Description: issues adjustment documents against a validated e-invoice.
Acceptance:
- Notes are generated from the canonical UBL of the original validated document (D-NOTES-001).
- The credit ledger runs SEED / RESERVE / CONFIRM / RELEASE / REVERSE, with `available ≥ 0` enforced by a database CHECK (D-NOTES-002).
- `line_kind` is `receipt_reversal` or `value_adjustment`, and value adjustments carry a `value_check` artefact (D-NOTES-003). The wording is **[PENDING D-EINV-010]**.
- Content and evidence hashes are kept separate, and canonical packages are retained in WORM for the statutory period (D-NOTES-004).
- `FILED` status requires an LHDN reference (D-FCORE-003).

**3. Compliance Calendar.** Description: a per-business calendar of e-invoice and SST obligations, with prepared actions.
Acceptance:
- Obligations and deadlines come only from the fact table. No dates are hard-coded (D-AUTOPILOT-001, D-DOCS-005).
- Each entry links to its readiness rows, nearest deadline first (D-READY-003).
- Obligations that don't apply show as declared N/A records (D-READY-002).
- The calendar prepares actions but never executes `file` or `submit` actions (D-AUTO-001, D-AUTOPILOT-001).
- **[OWNER-DECISION]** Notification lead times and channels (proposal: in-app plus email at 14, 7 and 2 days).

**4. Standing Approvals & Undo.** Description: lets the user pre-approve repeat bank categorisations under strict rules, with full undo.
Acceptance:
- Standing approvals exist only for `apply_internal` and bank categorisation (D-AUTO-002).
- The rule matches exactly on `payee_key ∈ approved_payee_set` AND direction AND amount band (D-AUTO-003).
- Payee keys are typed (biller, counterparty, name), with OR membership and a conflict guard (D-AUTO-004).
- Aliases are approved through the standing-approval authority, with retro-confirm or probation (D-AUTO-005).
- Every undo is reason-attributed and audited (D-AUTO-006, D-AUDIT-001).
- Soft review ends only on an explicit resume. Acknowledgements are period-scoped with a review-by date. On the third acknowledgement it becomes a hard block offering Resume, Edit or Revoke. Escalation is a soft nudge (D-AUTO-007).
- A tiered evidence screen is shown before approval (D-AUTO-008).
- No standing approval can ever cover `post_ledger`, `file`, `submit` or `external_send`.

**5. General Ledger.** Description: per-account transaction listing for a period.
Acceptance:
- Shows opening balance, each posting, running balance and closing balance per account.
- Closing balances equal the Trial Balance for the same period.
- Each line drills through to its source document and audit trail.
- Exports to PDF and Excel (D-REPORTS-001).
- MYR only (D-SCOPE-014).
- **[OWNER-DECISION]** Column set and filters (proposal: date, reference, description, counterparty, debit, credit, balance, tax code; filter by account range, period and source type).

## B2. New slice — Privacy & Compliance Evidence (milestone: Platform & Core Infrastructure)

Owner: DPO, with Legal Counsel co-signing.

Slice verification:
- A DPIA is approved before pilot.
- A breach drill completes inside the 72h path.
- Every artefact set is activated by a fact-checked PR.
- The probe fails closed.

| # | Feature | Acceptance (sources) |
|---|---|---|
| B2.1 | DPIA & Automated-Decision Assessment | DPIA covering AI extraction and categorisation as automated decision-making. AI is never the sole decider. Approved by the DPO before pilot (D-PRIV-003) |
| B2.2 | Breach Response Runbook | Commissioner notified within 72h; individuals within 7 days of that notice where harm is significant; DPO-owned; linked from the OPS incident runbook; one drill passed (D-PRIV-002, D-OPS-002) |
| B2.3 | Compliance Fact Table & Probe | Single source for rates, thresholds and deadlines. Residency-critical fields are api-only. Per-row probe status `ok`/`absent`/`error`, fail-closed, with a signed report (D-DOCS-004, D-DOCS-005) |
| B2.4 | Artefact Sets & Evidence Store | Sets A, B, B-split and C stored at `docs/compliance/artefacts/<set>/v<N>/`. DPO pre-approval; activation PR with CI fact-check; WORM evidence store with a repo index; offline verifier; DPO-approved export bundles; replicated archive (D-DOCS-001/002/003/006) |

> **Option:** the DPO may prefer to create only the slice now and add these features later. B2 would then mint 1 code and the total would be 6. Choose one before the CTO applies anything.

## B3. Corrections to existing items (before → after)

| # | Target (name) | Field | Before (verbatim from the 2026-10-24 paste) | After | Source | Owner |
|---|---|---|---|---|---|---|
| C1 | Mission | Description | "…integrates compliance (MyInvois e-invoicing, SST, statutory payroll) directly into the core product." | "…integrates compliance (MyInvois e-invoicing, SST) directly into the core product." | D-SCOPE-010 | CEO |
| C2 | SST Tax Codes | Description | "Define SST tax codes (ZR, SR, ZS, etc.) and apply to transactions." | "Define SST tax codes mapped 1:1 to MyInvois tax types (sales tax, service tax, tourism tax, high-value goods tax, low value goods tax, not applicable, exempt) and apply to transactions. No GST-era codes." | D-SST-002 | Tax Specialist |
| C3 | Web & Camera Capture | Acceptance (feature and milestone level) | "Extraction accuracy ≥70% approved without edits; image attached to entry; supports BM/English/Chinese." | "Correctness gate: precision ≥98% on total, SST and date with abstention, Wilson LB ≥95% per tier (D-EVAL-002). Automation KPI: ≥70% of captures approved without edits. Image attached to entry; supports BM/English/Chinese." | D-CAPTURE-003, D-EVAL-002 | AI Engineer + Data Lead |
| C4 | Bank Import | Description | "Import statements via file upload or direct bank feed (MYR only)." | "Import bank statements via file upload (CSV/OFX/PDF per bank), MYR only. No direct feeds." | D-SCOPE-025, D-BANK-001 | Product Manager |
| C5 | Bank Import | Acceptance | "Supported formats parsed; transactions listed; secure credentials stored." | "Supported formats parsed; transactions listed; no bank credentials stored." | D-SCOPE-025 | Product Manager |
| C6 | Traffic Light Dashboard | Description | "Visual indicator of filing status: green (ready), yellow (warnings), red (blockers)." | "Visual indicator of filing status: green (ready), amber (risk), red (blocker), grey (declared N/A with reason)." | D-READY-002 | Product Manager |
| C7 | Traffic Light Dashboard | Acceptance | "Status updates in real-time; click through to resolve issues; supports e-Invois and SST rows." | "Status updates in real time; rows sorted nearest deadline first; click through to resolve issues; supports e-Invoice and SST rows; N/A auto-downgrades on conflicting evidence." | D-READY-002/003 | Product Manager |
| C8 | Quotations & Invoices | Acceptance | "…e-invoice generation via MyInvois; payment reminders; supports consolidated B2C e-invoices." | "…e-invoice generation via MyInvois; payment reminders **[PENDING D-SALES-003]**; supports consolidated B2C e-invoices." | D-SALES-003 | Product Manager |
| C9 | Audit Events (G17) | Acceptance | "All events present; GDPR/PDPA compliant; …" | "All events present; PDPA compliant; …" | D-PRIV-001 | Architecture Lead |

## B4. Cross-mission links

| Link | From (name) | To | Type | Source |
|---|---|---|---|---|
| L1 | K8s/IRSA runtime slice(s), M-MVIJWNII-0005-29TQ | Development Environment & CI/CD | superseded-by | D-PLAT-002, D-PLAT-010 |
| L2 | Tenancy-kernel slice, M-MVIJWNII-0005-29TQ | Multi-tenant Kernel & Authentication | superseded-by | D-PLAT-010 |
| L3 | Audit-log slice, M-MVIJX5F9-000O-MY23 | Audit Events (G17) feature | superseded-by **or** depends-on **[PENDING D-AUDIT-003]** | D-AUDIT-003 |
| L4 | Firm-beachhead slice, M-MVIJX5F9-000O-MY23 | — | status → parked | D-SCOPE-018 |
| L5 | Document Capture | Eval-harness slice, M-MVIJWODE-0007-QN4Z | depends-on | D-EVAL-006 |
| L6 | Document Capture, Bank Reconciliation | Gateway slice, M-MVIJWODE-0007-QN4Z | depends-on | D-GW-001 |
| L7 | Each superseded slice | Its Core target | reverse link (two-way) | plan-lint |
