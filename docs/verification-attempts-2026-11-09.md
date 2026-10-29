# Verification Attempts Log – 2026-11-09

## REG-02 – AMLA (Anti-Money Laundering) Verification
- **Date:** 2026-11-09
- **Method:** Direct web fetch to Bank Negara Malaysia AML/CFT portal (`https://www.bnm.gov.my/web/amlcft`)
- **Result:** Portal reachable (HTTP 200). Extracted key facts:
  - **Record‑keeping retention period:** 6 years (post‑transaction or termination) – differs from design doc's 7‑year claim.
  - **Suspicious Transaction Report (STR) filing:** Must be submitted within the next working day of suspicion; reporting to FIED (Bank Negara Malaysia).
  - **Cash Threshold Report (CTR) threshold:** RM25,000 per day per customer for selected reporting institutions (banks, DFIs, LHDN, Lembaga Tabung Haji, licensed casino).
  - **Reporting institution categories:** Listed on BNM page – includes licensed banks, investment banks, Islamic banks, approved financial advisers/insurance brokers, licensed takaful operators, approved money‑brokers, designated payment instruments issuers, development financial institutions, securities/de derivatives firms, Labuan financial institutions, licensed money services businesses, trust companies, moneylenders, pawnbrokers, estate agents, precious metals/stone dealers, digital currency exchangers, gambling services (licensed casino, betting), accountants/legal practitioners, etc.
- **Verification Flag:** Updated REG‑02 status to **◐ DIRECTIONAL** (source reachable, specific implementation‑critical values confirmed). Still carries `⚠️ MUST BE VERIFIED AGAINST https://www.amla.gov.my` flag because BNM is the competent authority; the official AMLA consolidation was not directly reachable.
- **Status Change:** ⚠️ KNOWLEDGE‑BASED → ◐ DIRECTIONAL
- **Notes:** Discrepancy noted: design document claimed 7‑year record‑keeping; BNM specifies 6 years. This requires engineering update to align retention period in audit‑log design and related data‑model defaults.

---

*Prepared by Legal & Regulatory Counsel (agent-47c095b2)*