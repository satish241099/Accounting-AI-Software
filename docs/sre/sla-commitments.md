# SLA Commitments — Malaysia Accounting SaaS

## Service Tiers and Uptime Commitments

| Service Tier | Services Included | Uptime Commitment | Credit Trigger | Credit Amount |
|---|---|---|---|---|
| **Core Compliance** | e-Invois API, LHDN filing, statutory payroll (EPF/SOCSO/EIS/HRD Corp/PCB), SST returns | **99.5%** | Availability < 99.5% for the billing month | 5% of monthly subscription fee |
| **Auth** | Authentication/authorization (Entra ID integration, token management, MFA) | **99.9%** | Availability < 99.9% for the billing month | 3% of monthly subscription fee |
| **Standard API** | General API endpoints (CRUD, query, AI copilot calls) | **99.5%** | Availability < 99.5% for the billing month | 5% of monthly subscription fee |

## SLA Calculation

- **Billing month:** Calendar month (00:00 UTC on the 1st to 23:59 UTC on the last day).
- **Availability = (Successful requests / Total requests) × 100**, computed per the measurement definition in `docs/sre/slos.md` (30‑day rolling window, but SLA is evaluated per-billing-month for credit purposes).
- **Exclusions:** Scheduled maintenance windows published at least 48 hours in advance by the provider are excluded from the SLA calculation, consistent with the SLO exclusion windows for LHDN e-Invois maintenance.

## LHDN e-Invois Regulatory Availability Windows

- **Maintenance windows:** LHDN publishes e-Invois system maintenance schedules at least 48 hours in advance via the MyInvois developer portal.
- **Exclusion from SLA:** During any published maintenance window, requests to the e‑Invois API are excluded from both availability numerator and denominator for SLA credit evaluation.
- **Regulatory availability commitment:** The e‑Invois API is available for filing during LHDN‑published business hours (typically 09:00–18:00 MYT, Monday–Friday, excluding Malaysian public holidays). Downtime outside these windows does not trigger SLA credits, though it still counts toward the SLO 99.5% target.
- **Force‑majeure:** Acts beyond reasonable control (e.g., LHDN system outage, internet backbone failure in ap-southeast-1) are documented and may be subject to a separate SLA review.

## Service‑Tier Descriptions

### Core Compliance
- **Purpose:** The tier covering all LHDN‑mandated filing and statutory compliance obligations.
- **In-scope services:** e‑Invois API submission and status, LHDN statutory filing windows, EPF/SOCSO/EIS/HRD Corp/PCB payroll statutory returns, SST return filing.
- **Customer value:** Guaranteed availability for the compliance‑critical path; without this tier, customers cannot reliably file e‑invoices or statutory returns.

### Auth
- **Purpose:** Guarantees the availability of the authentication service that underpins all other tiers.
- **In-scope services:** Entra ID‑based login, JWT token issuance and validation, MFA challenges, session management, token refresh (within the 60‑minute expiry window).
- **Customer value:** Protects the entire application from auth outages that would lock out all users, including accountants and SME administrators.

### Standard API
- **Purpose:** General API availability for all non‑compliance, non‑auth operations.
- **In-scope services:** All API routes not classified as e‑Invois or auth (CRUD operations, AI copilot queries, data exports, onboarding flows).
- **Customer value:** A baseline availability guarantee for the general user experience.

## Credit Policy

- **Credit trigger:** SLA availability measured per billing month falls below the committed uptime target.
- **Credit amount:** Percentage of the customer's monthly subscription fee, as shown in the table above.
- **Credit issuance:** Credits are applied to the next billing cycle automatically; no manual request required.
- **Credit cap:** Total credits per billing month are capped at 10% of the monthly subscription fee, even if multiple tiers fall below their targets in the same month.
- **Exclusions:** Credits do not apply when downtime is caused by:
  - Published LHDN maintenance windows (excluded per the SLA exclusion rule).
  - Customer‑side network failures or internet outages.
  - Force‑majeure events beyond reasonable control.
  - Usage exceeding defined rate limits or quotas.

## PDPA Data Residency & Azure Malaysia Hosting Constraints

- **All SLA measurements and credit calculations are based on data hosted in** **ap‑southeast‑1** (Azure Malaysia region), per PDPA 2024 requirements.
- **Cross‑region failover:** In the event of a region‑wide Azure outage, SLA credit evaluation uses the last known healthy region (ap‑southeast‑1). Failover to another region is documented and does not automatically trigger credits.
- **Data residency guarantee:** No customer data is stored or processed outside ap‑southeast‑1. SLA metrics reflect only requests served from the Malaysia region; external requests are routed through the regional gateway.
- **Audit:** SLA compliance reports are stored in ap‑southeast‑1 and are accessible to customers on request, with redactions per PDPA 2024 §22.

## SLA Reporting

- **Monthly SLA report:** Generated within 5 business days of the billing month close, showing:
  - Availability per tier (percentage).
  - Total downtime (minutes) per tier.
  - Credit eligibility and amount (if any).
  - Breakdown of excluded maintenance windows.
- **Customer access:** Reports are available in the customer dashboard under "Compliance & SLA" for the current and prior three billing months.
- **Dispute window:** Customers may dispute an SLA report within 15 business days of generation; disputes are reviewed by the SRE lead within 10 business days.

## References

- ACCO-012 SLO baseline and existing audit‑log alert references
- PDPA 2024 — data residency: ap‑southeast‑1 requirement
- LHDN e‑Invois business hours and maintenance window publications
- Azure Malaysia region (ap‑southeast‑1) service availability SLA