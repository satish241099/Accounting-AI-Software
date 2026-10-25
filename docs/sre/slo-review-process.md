# Monthly SLO Review & Postmortem Process — Malaysia Accounting SaaS

## Review Cadence

| Item | Detail |
|---|---|
| **Frequency** | Monthly, within 5 business days of the month close (aligned to the SLA report generation cycle). |
| **Timing** | First Thursday of each month, 10:00 MYT, 60‑minute block. |
| **Duration** | 60 minutes maximum. |
| **Recorded** | Meeting notes stored in the task document linked to the mission feature `F-SRE-024`; recording optional, notes mandatory. |

### Attendees

| Role | Attendee |
|---|---|
| **SRE Lead** (facilitator) | Agent-3bdca2fd (SRE Engineer) |
| **Platform Engineer** | Owner of the service(s) under review |
| **Product Manager** | Accountability for release decisions and error budget consumption |
| **Engineering Manager** | Authority to approve release unfreezes and resource reallocation |
| **Compliance Officer** (optional, quarterly) | LHDN regulatory alignment verification |
| **Notes scribe** | Rotating among the team; notes stored in task documents. |

### Metrics Source

- **Primary source:** `docs/sre/slos.md` SLO definitions and the availability metrics computed by the SRE monitoring pipeline (Prometheus + Grafana, backed by the audit‑log chain hashes for tamper evidence).
- **Secondary source:** Billing‑month SLA report generated from the same metrics (see `docs/sre/sla-commitments.md`).
- **Data cutoff:** All metrics as of 23:59 UTC on the last day of the preceding month; any incidents ongoing after the cutoff are marked "pending follow‑up" in the next review.

### Acceptance Criteria

The review is **accepted** when all of the following are confirmed:

1. **SLO status documented:** Each SLO (e‑Invois API 99.5%, auth 99.9%, general API 99.5%) is reported as either "at target" or "below target" with the actual availability percentage for the month.
2. **Error budget consumption reviewed:** Current burn rate for each SLO is compared against the 1x, 2x, and 5x thresholds defined in `docs/sre/error-budgets.md`. Any threshold crossed since the last review is flagged.
3. **Incident summary complete:** All incidents that contributed to SLO degradation are listed with severity, duration, and root cause (if known).
4. **Action items assigned:** Each identified action item has an owner, due date, and acceptance criteria — recorded in the task document linked to the mission feature.
5. **Postmortem status verified:** Any postmortems from the prior 90‑day window are verified complete (RCA, remediation, error budget recovery plan documented and implemented).

If any acceptance criterion is not met, the review is **deferred** and rescheduled within 5 business days with a clear remediation path.

## SLO Breach Trigger: Postmortem Within 72h

### Trigger Condition

An SLO breach is declared when **any** of the following is true for the rolling 30‑day window:

- e‑Invois API availability < 99.5%
- Auth availability < 99.9%
- General API availability < 99.5%

### Postmortem Process

| Step | Owner | Deadline | Deliverable |
|---|---|---|---|
| **1. Incident declaration** | SRE Lead | Immediately upon breach detection | Slack/PagerDuty P1 alert; "SLO breach" tag added to the incident ticket. |
| **2. RCA start** | Platform Engineer (service owner) | Within 24h of declaration | Root cause analysis document (max 2 pages) — what, when, where, why, how. |
| **3. RCA completion** | Platform Engineer | Within 48h of declaration | Full RCA with timeline, contributing factors, and failure mode classification. |
| **4. Remediation plan** | Platform Engineer + Engineering Manager | Within 48h of declaration | Actionable remediation items with owners and due dates; error budget recovery plan describing how the budget will be replenished. |
| **5. Postmortem write‑up** | SRE Lead | Within 72h of declaration | Structured postmortem document (see template below) stored in the mission feature task document. |
| **6. Review & close** | SRE Lead + Engineering Manager | Within 72h of declaration (or as soon as all items are complete) | Sign‑off that the remediation is implemented and the postmortem is complete. |

### Postmortem Template (stored in `docs/sre/slo-review-process.md` artifact)

```
# Postmortem: SLO Breach — <SLO name> — <Month Year>

## 1. Summary (2‑3 sentences)
What happened, which SLO was breached, and the impact on customers.

## 2. Timeline
- <Timestamp>: Incident detected
- <Timestamp>: SLO breach declared
- <Timestamp>: RCA started
- <Timestamp>: RCA completed
- <Timestamp>: Remediation implemented
- <Timestamp>: Postmortem signed off

## 3. Root Cause
- Immediate cause: <e.g., 5xx spike from MyInvois SDK certificate expiry>
- Contributing factors: <e.g., insufficient monitoring alert threshold, missing integration test>
- systemic issue: <e.g., single‑point dependency on external certificate renewals>

## 4. Remediation
- <What was changed to prevent recurrence>
- <Error budget recovery plan: how the consumed budget will be recovered>

## 5. Action Items
| ID | Action | Owner | Due Date | Status |
|---|---|---|---|---|
| AC-001 | <description> | <name> | <date> | <open/closed> |

## 6. Prevention
- <What process or system change will prevent a recurrence, e.g., alert threshold adjustment, integration test addition, certificate auto‑renewal pipeline>

## 7. Sign‑off
- SRE Lead: _______________________  Date: _________
- Engineering Manager: _______________________  Date: _________
```

### Review Artifact Template and Storage Location

- **Artifact title:** `Monthly SLO Review Notes — <Month Year>`
- **Storage location:** Task document attached to the mission feature `F-SRE-024` (SLOs & Error Budgets), key=`slo-review-notes`.
- **Metadata captured per review:**
  - Review date and attendees.
  - SLO status for each of the three targets.
  - Error budget burn rates at 1x, 2x, 5x.
  - Incident list with severities and durations.
  - Action items with owners and due dates.
  - Postmortem status (complete/pending).
  - Next review date.

- **Access control:** The task document is project‑scoped and requires valid `app.tenant_id` RLS context for access (per `docs/audit-log-design.md` audit‑log RLS policies). Compliance officers and the engineering manager have read/write access; all other roles have read‑only.

## Quarterly Review Deep‑Dive

In addition to the monthly review, a **quarterly deep‑dive** is held (optional Compliance Officer attendance):

- Reviews 90‑day trend data for each SLO.
- Evaluates whether SLO targets remain aligned to LHDN e‑Invois regulatory availability windows and any changes in MyInvois SDK terms.
- Assesses error budget consumption patterns and whether budget recovery plans are effective.
- Recommends SLO target adjustments (up or down) for the next quarter, documented as a task refinement.
- Quarterly deep‑dive notes are stored in the same task document, tagged with `quarterly-deep-dive`.

## References

- ACCO-012 SLO baseline and existing audit‑log alert references
- `docs/sre/slos.md` — SLO definitions and error definitions
- `docs/sre/error-budgets.md` — Budget calculations, burn‑rate thresholds, release freeze rules
- `docs/sre/sla-commitments.md` — SLA credit policy and LHDN maintenance window exclusions
- PDPA 2024 — retention and alerting obligations