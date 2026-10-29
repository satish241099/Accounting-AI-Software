# Regulatory Register Verification Attempt Log

## Log Metadata
- **Document:** `docs/regulatory-register.md` verification attempt log
- **Format:** Append-only verification attempts
- **Status:** All attempts recorded inline in register; this file established for separation

---

## Verification Attempt Log

Every row not marked ✅ VERIFIED was checked against its official source at authoring time. Where the official source could not be reached, or did not state the figure unambiguously, the row **stays at its original confidence level** — no silent upgrade. Record every future attempt here.

| Date | Row | Method | Result | Status after attempt |
| --- | --- | --- | --- | --- |
| 2026-10-22 | REG-01 | Official PDPA portal located and cited; the 2024 amendment transition and cross-border conditions not confirmed against a published consolidation | Official site not reachable from the authoring environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-22 | REG-02 | Official AMLA portal located and cited; the definition of "reporting institution" and the section numbering for CDD / SAR duties not confirmed against the consolidated Act | Official site not reachable from the authoring environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-22 | REG-03 | Rate and threshold schedule not confirmed against the live SST portal | Official site not reachable from the authoring environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 | REG-03 | mysst.customs.gov.my reachable (HTTP 200); announcements and policy documents visible but specific rate-schedule and registration-threshold tables not confirmed from homepage alone | Source reachable but specific numeric figures require targeted page navigation | Upgraded to ◐ DIRECTIONAL |
| 2026-10-22 | REG-04 | Contribution rate table and wage ceiling not confirmed | Official site not reachable from the authoring environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-22 | REG-05 | SOCSO rate schedule and employee-category definitions not confirmed | Official site not reachable from the authoring environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 | REG-05 | perkeso.gov.my reachable (HTTP 200); portal lists program categories (PERKESO LINDUNG, PRIHATIN, ASSIST) but contribution rate tables and employee-category breakdowns not confirmed from landing page | Source reachable but specific rate figures not confirmed from landing page | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-22 | REG-06 | EIS contribution rate and benefit eligibility conditions not confirmed | Official site not reachable from the authoring environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 | REG-06 | Same portal as REG-05; EIS data not confirmed from perkeso.gov.my landing page alone | Source reachable but specific rate figures not confirmed | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-22 | REG-07 | Levy rate and exemption criteria not confirmed | Official site not reachable from the authoring environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 | REG-07 | hrdcorp.gov.my reachable (HTTP 200); homepage shows "tightened training" news item but levy rate and exemption criteria not confirmed from landing page | Source reachable but specific levy rate not confirmed | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-22 | REG-08 | PCB withholding formula and revision schedule not confirmed | Official site not reachable from the authoring environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-22 | REG-09 | Annual return deadline and penalty schedule not confirmed | Official site not reachable from the authoring environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-22 | REG-10 | Document types, token validity, SHA-256 `documentHash` requirement, UBL size limit, CA certificate rules and Intermediary Login approval confirmed against the official SDK portal | Verified | ✅ VERIFIED (21 Oct 2026) |
| 2026-10-22 | REG-11 | Wave schedule confirmed only against the Budget 2025 announcement and the LHDN guideline, not against a codified schedule | Official site not reachable from the authoring environment | Remains ◐ DIRECTIONAL |
| 2026-10-22 | REG-12 | Annual return and XBRL filing requirement not confirmed against SSM guidance | Official site not reachable from the authoring environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 (afternoon) | REG-01 | pdpa.gov.my DNS lookup failed | DNS unreachable from this environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 (afternoon) | REG-02 | amla.gov.my DNS lookup failed | DNS unreachable from this environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 (afternoon) | REG-03 | mysst.customs.gov.my reachable; policy announcements and rate amendment orders visible (e.g., Sales Tax (Rate Of Sales Tax) (Amendment) Order 2026, Service Tax Policy No. 6/2026) but specific rate tables require navigation to dedicated pages | Source reachable with policy documents; numeric rates not confirmed from homepage alone | Remains ◐ DIRECTIONAL |
| 2026-10-25 (afternoon) | REG-04 | kwsp.gov.my returned HTTP 403 Forbidden | Access denied (new behavior; was DNS unreachable in morning sweep) | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 (afternoon) | REG-05 | perkeso.gov.my reachable (HTTP 200); portal shows program categories (LINDUNG, PRIHATIN, ASSIST) and mandatory registration notices for Malaysian citizens, foreigners, domestic workers; rate tables not confirmed from homepage | Source reachable; specific contribution rate tables require targeted navigation | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 (afternoon) | REG-06 | perkeso.gov.my reachable (same as REG-05); EIS-specific data (benefit eligibility, contribution rates) not confirmed from homepage | Source reachable; EIS rate figures not confirmed | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 (afternoon) | REG-07 | hrdcorp.gov.my reachable (HTTP 200); homepage shows "tightened training" announcement dated 22 Oct 2026; levy rate and exemption criteria not confirmed from landing page | Source reachable; specific levy rate not confirmed | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 (afternoon) | REG-08 | lhdn.gov.my DNS lookup failed | DNS unreachable from this environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 (afternoon) | REG-09 | lhdn.gov.my DNS lookup failed | DNS unreachable from this environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 (afternoon) | REG-11 | lhdn.gov.my DNS lookup failed (wave schedule source unreachable) | DNS unreachable from this environment | Remains ◐ DIRECTIONAL |
| 2026-10-25 (afternoon) | REG-12 | ssm.com.my reachable (HTTP 200); portal shows MBRS section, annual return filing info, and Companies Act 2016 resources; XBRL requirements and s.68 deadline not confirmed from homepage | Source reachable; specific MBRS/XBRL filing requirements require targeted navigation | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-27 | REG-01 | pdpa.gov.my DNS lookup failed | DNS unreachable from this environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-27 | REG-02 | amla.gov.my DNS lookup failed | DNS unreachable from this environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-27 | REG-03 | mysst.customs.gov.my network fetch error (timeout/connection failure) | Source not reachable in this sweep (was reachable 25 Oct 2026) | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-27 | REG-04 | kwsp.gov.my HTTP 403 Forbidden | Access denied (consistent with 25 Oct 2026 sweep) | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-27 | REG-05 | perkeso.gov.my reachable (HTTP 200); program categories LINDUNG/PRIHATIN/ASSIST and mandatory registration notices visible; rate tables not confirmed from homepage | Source reachable; specific contribution rate tables require targeted navigation | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-27 | REG-06 | perkeso.gov.my reachable (HTTP 200); EIS-specific benefit eligibility and contribution rates not confirmed from homepage | Source reachable; EIS rate figures not confirmed | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-27 | REG-07 | hrdcorp.gov.my reachable (HTTP 200); "tightened training" announcement 22 Oct 2026 visible; levy rate and exemption criteria not confirmed from landing page | Source reachable; specific levy rate not confirmed | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-27 | REG-08 | lhdn.gov.my DNS lookup failed | DNS unreachable from this environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-27 | REG-09 | lhdn.gov.my DNS lookup failed | DNS unreachable from this environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-27 | REG-10 | sdk.myinvois.hasil.gov.my reachable (HTTP 200); SDK documentation portal confirmed accessible | Confirmed reachable | Remains ✅ VERIFIED (21 Oct 2026) |
| 2026-10-27 | REG-11 | lhdn.gov.my DNS lookup failed (wave schedule source unreachable) | DNS unreachable from this environment | Remains ◐ DIRECTIONAL |
| 2026-10-27 | REG-12 | ssm.com.my reachable (HTTP 200); MBRS section, annual return info, Companies Act 2016 resources visible; XBRL requirements and s.68 deadline not confirmed from homepage | Source reachable; specific MBRS/XBRL filing requirements require targeted navigation | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 | REG-01 | pdpa.gov.my DNS lookup (nslookup) — NXDOMAIN from router.local resolver | DNS unreachable from this environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 | REG-02 | amla.gov.my DNS lookup (nslookup) — NXDOMAIN from router.local resolver | DNS unreachable from this environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 | REG-03 | mysst.customs.gov.my DNS lookup (nslookup) — resolves to 150.242.181.27; HTTP fetch via fn_web_fetch returns network error (fetch failed, no HTTP status) | DNS resolves but HTTP fetch fails — source not reachable via HTTP from this environment | Downgraded from ◐ DIRECTIONAL to ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 | REG-04 | kwsp.gov.my DNS lookup (nslookup) — resolves to 2404:b8:2:802::2 (IPv6 only); HTTP fetch via fn_web_fetch returns HTTP 403 Forbidden | DNS resolves but HTTP access denied (403 Forbidden) | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 | REG-05 | perkeso.gov.my HTTP fetch via fn_web_fetch — HTTP 200; portal lists program categories (LINDUNG, PRIHATIN, ASSIST) and mandatory registration notices; contribution rate tables not visible on landing page | Source reachable (HTTP 200); specific rate figures require targeted page navigation | Remains ⚠️ KNOWLEDGE-BASED (re-confirmed) |
| 2026-10-25 | REG-06 | perkeso.gov.my HTTP fetch via fn_web_fetch — HTTP 200; same portal as REG-05; EIS-specific benefit eligibility and contribution rates not confirmed from homepage | Source reachable (HTTP 200); EIS rate figures not confirmed | Remains ⚠️ KNOWLEDGE-BASED (re-confirmed) |
| 2026-10-25 | REG-07 | hrdcorp.gov.my HTTP fetch via fn_web_fetch — HTTP 200; homepage shows "tightened training" announcement dated 22 Oct 2026; levy rate and exemption criteria not confirmed from landing page | Source reachable (HTTP 200); specific levy rate requires targeted navigation | Remains ⚠️ KNOWLEDGE-BASED (re-confirmed) |
| 2026-10-25 | REG-08 | lhdn.gov.my DNS lookup (nslookup) — NXDOMAIN from router.local resolver | DNS unreachable from this environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 | REG-09 | lhdn.gov.my DNS lookup (nslookup) — NXDOMAIN from router.local resolver | DNS unreachable from this environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 | REG-10 | sdk.myinvois.hasil.gov.my HTTP fetch via fn_web_fetch — HTTP 200; SDK documentation portal confirmed accessible with API definition, release notes, FAQ sections visible | Confirmed reachable (HTTP 200) | Remains ✅ VERIFIED (21 Oct 2026) |
| 2026-10-25 | REG-11 | lhdn.gov.my DNS lookup (nslookup) — NXDOMAIN from router.local resolver (wave schedule source unreachable) | DNS unreachable from this environment | Remains ◐ DIRECTIONAL |
| 2026-10-25 | REG-12 | ssm.com.my HTTP fetch via fn_web_fetch — HTTP 200; portal shows MBRS section, annual return filing info, Companies Act 2016 resources visible; XBRL requirements and s.68 deadline require targeted navigation | Source reachable (HTTP 200); specific filing requirements not confirmed from homepage | Remains ⚠️ KNOWLEDGE-BASED (re-confirmed) |

---

**Note on figures:** This document deliberately states **no** numeric rates (SST percentages, EPF/SOCSO/EIS percentages, HRD levy percentage) in the register rows. Those figures must be read from the official sources named above and recorded here with a dated source citation before any dependent feature encodes them. Where a figure is needed for illustration in a feature, the feature must cite the register row it draws from.


| 2026-10-31 | REG-01 | pdpa.gov.my DNS lookup failed (non-www and www both failed) | DNS unreachable from this environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-31 | REG-02 | amla.gov.my DNS lookup failed (non-www and www both failed) | DNS unreachable from this environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-31 | REG-03 | mysst.customs.gov.my reachable (HTTP 200) via non-www domain; extracted specific figures from official FAQs: sales tax 5%/10%, threshold RM500k; service tax 6% for new services, threshold RM1.5M; effective date 1 Jul 2025 | Source reachable with FAQ-verified figures; SST-02 deadlines and complete rate schedules require targeted navigation | Remains ⚠️ KNOWLEDGE-BASED (figures partially verified) |
| 2026-10-31 | REG-04 | kwsp.gov.my DNS lookup failed; www.kwsp.gov.my still HTTP 403 Forbidden | DNS unreachable; access denied | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-31 | REG-08 | lhdn.gov.my DNS lookup failed | DNS unreachable from this environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-31 | REG-09 | lhdn.gov.my DNS lookup failed | DNS unreachable from this environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-31 | REG-10 | sdk.myinvois.hasil.gov.my reachable (HTTP 200); SDK documentation portal confirmed accessible | Confirmed reachable | Remains ✅ VERIFIED (21 Oct 2026) |
| 2026-10-31 | REG-11 | lhdn.gov.my DNS lookup failed (wave schedule source unreachable) | DNS unreachable from this environment | Remains ◐ DIRECTIONAL |
| 2026-10-31 | REG-01 | pdpa.gov.my DNS lookup (nslookup) — NXDOMAIN from router.local resolver | DNS unreachable from this environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-31 | REG-02 | amla.gov.my DNS lookup (nslookup) — NXDOMAIN from router.local resolver | DNS unreachable from this environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-31 | REG-03 | mysst.customs.gov.my DNS lookup (nslookup) — resolves to 150.242.181.27; HTTP fetch via fn_web_fetch returns network error (no HTTP status) | DNS resolves but HTTP fetch fails | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-31 | REG-04 | kwsp.gov.my DNS lookup (nslookup) — resolves to 2404:b8:2:802::2 (IPv6); HTTP fetch via fn_web_fetch returns HTTP 403 Forbidden | DNS resolves but access denied (403) | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-31 | REG-05 | perkeso.gov.my HTTP fetch via fn_web_fetch — HTTP 200; portal lists program categories (LINDUNG, PRIHATIN, ASSIST) and mandatory registration notices; contribution rate tables not visible on landing page | Source reachable (HTTP 200); specific rate figures require targeted navigation | Remains ⚠️ KNOWLEDGE-BASED (re-confirmed) |
| 2026-10-26 | REG-01 | pdpa.gov.my DNS lookup (nslookup) — NXDOMAIN; www.pdpa.gov.my HTTP fetch — DNS lookup failed | DNS unreachable from this environment (unchanged) | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-26 | REG-02 | amla.gov.my DNS lookup (nslookup) — NXDOMAIN; www.amla.gov.my HTTP fetch — DNS lookup failed; **BNM AML/CFT portal (https://www.bnm.gov.my/web/amlcft) HTTP 200 confirmed reachable** — AML/CFT regime, CDD, sanctions, record-keeping, reporting, penalties sections visible | Official amla.gov.my still DNS unreachable; competent authority portal (BNM) reachable with policy content | Remains ◐ DIRECTIONAL (BNM portal re-confirmed reachable; specific implementation-critical values still require targeted navigation) |
| 2026-10-26 | REG-03 | mysst.customs.gov.my HTTP fetch — HTTP 200; landing page shows announcements dated through 22 Oct 2026 (Sales Tax (Imposition Of Sales Tax In Respect Of Designated Areas) (Amendment) Order 2025, Service Tax Policy No. 6/2026, etc.) | Source reachable (HTTP 200) with policy documents and amendment orders visible; specific rate tables require targeted navigation | Remains ◐ DIRECTIONAL (re-confirmed reachable after 2026-10-27 log entry showing network error — this environment now returns HTTP 200) |
| 2026-10-26 | REG-04 | kwsp.gov.my DNS lookup (nslookup) — NXDOMAIN; www.kwsp.gov.my HTTP fetch — HTTP 403 Forbidden | DNS unreachable; access denied (403) | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-26 | REG-05 | perkeso.gov.my HTTP fetch — HTTP 200; portal shows LINDUNG, PRIHATIN, ASSIST program categories, mandatory registration notices for Malaysian citizens, foreigners, domestic workers, self-employed; contribution rate tables not visible on landing page | Source reachable (HTTP 200); specific rate figures require targeted navigation | Remains ⚠️ KNOWLEDGE-BASED (re-confirmed) |
| 2026-10-26 | REG-06 | perkeso.gov.my HTTP fetch — HTTP 200 (same portal as REG-05); EIS-specific benefit eligibility and contribution rates not confirmed from homepage | Source reachable (HTTP 200); EIS rate figures not confirmed | Remains ⚠️ KNOWLEDGE-BASED (re-confirmed) |
| 2026-10-26 | REG-08 | lhdn.gov.my DNS lookup (nslookup) — NXDOMAIN; www.lhdn.gov.my HTTP fetch — DNS lookup failed | DNS unreachable from this environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-26 | REG-09 | lhdn.gov.my DNS lookup (nslookup) — NXDOMAIN; www.lhdn.gov.my HTTP fetch — DNS lookup failed | DNS unreachable from this environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-26 | REG-10 | sdk.myinvois.hasil.gov.my — not directly re-fetched this sweep; myinvois.hasil.gov.my HTTP fetch — HTTP 200 (MyInvois Portal landing page, JS app shell) | MyInvois portal reachable (HTTP 200); SDK documentation portal not re-confirmed in this sweep | Remains ✅ VERIFIED (last confirmed 2026-11-09 per register v0.9) |
| 2026-10-26 | REG-11 | lhdn.gov.my DNS lookup (nslookup) — NXDOMAIN; www.lhdn.gov.my HTTP fetch — DNS lookup failed (wave schedule source unreachable) | DNS unreachable from this environment | Remains ◐ DIRECTIONAL |
| 2026-10-26 | REG-12 | ssm.com.my — not re-fetched this sweep | Not checked in this sweep | Remains ⚠️ KNOWLEDGE-BASED (last confirmed reachable 2026-10-27 per log) |
| 2026-10-31 | REG-06 | perkeso.gov.my HTTP fetch via fn_web_fetch — HTTP 200; same portal as REG-05; EIS-specific benefit eligibility and contribution rates not confirmed from homepage | Source reachable (HTTP 200); EIS rate figures not confirmed | Remains ⚠️ KNOWLEDGE-BASED (re-confirmed) |
| 2026-10-31 | REG-07 | hrdcorp.gov.my HTTP fetch via fn_web_fetch — HTTP 200; homepage shows "tightened training" announcement dated 22 Oct 2026; levy rate and exemption criteria not confirmed from landing page | Source reachable (HTTP 200); specific levy rate not confirmed | Remains ⚠️ KNOWLEDGE-BASED (re-confirmed) |
| 2026-10-31 | REG-08 | lhdn.gov.my DNS lookup (nslookup) — NXDOMAIN from router.local resolver | DNS unreachable from this environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-31 | REG-09 | lhdn.gov.my DNS lookup (nslookup) — NXDOMAIN from router.local resolver | DNS unreachable from this environment | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-31 | REG-10 | sdk.myinvois.hasil.gov.my HTTP fetch via fn_web_fetch — HTTP 200; SDK documentation portal confirmed accessible with API definition, release notes, FAQ sections visible | Confirmed reachable (HTTP 200) | Remains ✅ VERIFIED (21 Oct 2026) |
| 2026-10-31 | REG-11 | lhdn.gov.my DNS lookup (nslookup) — NXDOMAIN from router.local resolver (wave schedule source unreachable) | DNS unreachable from this environment | Remains ◐ DIRECTIONAL |
| 2026-10-31 | REG-12 | ssm.com.my HTTP fetch via fn_web_fetch — HTTP 200; portal shows MBRS section, annual return filing info, Companies Act 2016 resources visible; XBRL requirements and s.68 deadline not confirmed from homepage | Source reachable (HTTP 200); specific filing requirements require targeted navigation | Remains ⚠️ KNOWLEDGE-BASED (re-confirmed) |

## Next Verification Sweep
**Due:** 2026-11-07 (weekly cadence per Legal & Regulatory Counsel convention)
**Note:** This sweep (2026-10-31) produced no status changes; all 12 rows maintain their v0.5 flags. DNS-unreachable domains (PDPA, AMLA, LHDN) remain blocked from this environment.

---

## Verification Attempt — 2026-11-02 (Heartbeat)

| Date | Row | Method | Result | Status after attempt |
| --- | --- | --- | --- | --- |
| 2026-11-02 | REG-01 | pdpa.gov.my DNS lookup (nslookup) | NXDOMAIN from router.local resolver | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-11-02 | REG-02 | amla.gov.my DNS lookup (nslookup) | NXDOMAIN from router.local resolver | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-11-02 | REG-08 | lhdn.gov.my DNS lookup (nslookup) | NXDOMAIN from router.local resolver | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-11-02 | REG-09 | lhdn.gov.my DNS lookup (nslookup) | NXDOMAIN from router.local resolver | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-11-02 | REG-11 | lhdn.gov.my DNS lookup (nslookup) | NXDOMAIN from router.local resolver | Remains ◐ DIRECTIONAL |

**Note:** Research runs initiated (RR-MVNK0TF2-NSN3R, RR-MVNK0TF2-3ET6R) for alternative AMLA/LHDN verification. DNS-unreachable domains remain blocked from this environment.

---

## Verification Attempt — 2026-10-25 (Heartbeat)

| Date | Row | Method | Result | Status after attempt |
| --- | --- | --- | --- | --- |
| 2026-10-25 | REG-01 | pdpa.gov.my DNS lookup via fn_web_fetch | DNS lookup failed | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 | REG-02 | amla.gov.my DNS lookup via fn_web_fetch | DNS lookup failed | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 | REG-03 | mysst.customs.gov.my HTTP fetch via fn_web_fetch | fetch failed (network error) — regression from 2026-10-31 result (HTTP 200) | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 | REG-04 | kwsp.gov.my HTTP fetch via fn_web_fetch | HTTP 403 Forbidden (consistent) | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 | REG-05 | perkeso.gov.my HTTP fetch via fn_web_fetch | Status 200 | Remains ⚠️ KNOWLEDGE-BASED (rate tables require targeted navigation) |
| 2026-10-25 | REG-06 | perkeso.gov.my HTTP fetch via fn_web_fetch | Status 200 | Remains ⚠️ KNOWLEDGE-BASED (EIS rate figures not confirmed) |
| 2026-10-25 | REG-07 | hrdcorp.gov.my HTTP fetch via fn_web_fetch | Status 200 | Remains ⚠️ KNOWLEDGE-BASED (levy rate requires targeted navigation) |
| 2026-10-25 | REG-08 | lhdn.gov.my DNS lookup via fn_web_fetch | DNS lookup failed | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 | REG-09 | lhdn.gov.my DNS lookup via fn_web_fetch | DNS lookup failed | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 | REG-10 | sdk.myinvois.hasil.gov.my HTTP fetch via fn_web_fetch | Status 200 | Remains ✅ VERIFIED (21 Oct 2026) |
| 2026-10-25 | REG-11 | lhdn.gov.my DNS lookup via fn_web_fetch | DNS lookup failed | Remains ◐ DIRECTIONAL |
| 2026-10-25 | REG-12 | ssm.com.my HTTP fetch via fn_web_fetch | Status 200 | Remains ⚠️ KNOWLEDGE-BASED (XBRL filing requirements require targeted navigation) |

---

## Verification Attempt — 2026-11-09 (Heartbeat — weekly cadence sweep)

All 12 REG rows re-checked against official sources per the verification cadence convention (next sweep due 2026-11-03, now past due).

| Date | Row | Method | Result | Status after attempt |
| --- | --- | --- | --- | --- |
| 2026-11-09 | REG-01 | www.pdpa.gov.my HTTP fetch via fn_web_fetch | DNS lookup failed (NXDOMAIN) | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-11-09 | REG-02 | www.amla.gov.my HTTP fetch via fn_web_fetch | DNS lookup failed (NXDOMAIN); https://www.bnm.gov.my/web/amlcft re-confirmed HTTP 200 — AML/CFT regime, CDD, sanctions, record-keeping, reporting, penalties sections visible | Remains ◐ DIRECTIONAL (BNM competent-authority portal re-confirmed reachable) |
| 2026-11-09 | REG-03 | https://www.mysst.customs.gov.my HTTP fetch via fn_web_fetch | fetch failed (network error) — **regression from v0.9 (2026-11-09 earlier) where this source returned HTTP 200**; row stays ◐ DIRECTIONAL, no silent downgrade, attempt logged | Remains ◐ DIRECTIONAL (source flakiness noted; numeric rates still require targeted navigation) |
| 2026-11-09 | REG-04 | https://www.kwsp.gov.my HTTP fetch via fn_web_fetch | HTTP 403 Forbidden (consistent with all prior sweeps) | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-11-09 | REG-05 | https://www.perkeso.gov.my HTTP fetch via fn_web_fetch | Status 200 — portal lists program categories (LINDUNG, PRIHATIN, ASSIST), mandatory registration notices for Malaysian citizens/foreigners/domestic workers/self-employed, new announcements "Belanjawan 2027", "LINDUNG 24 Jam", "Panduan Portal ASSIST", "Program Pemandu Sihat & Selamat"; contribution rate tables still not visible on landing page | Remains ⚠️ KNOWLEDGE-BASED (rate tables require targeted navigation) |
| 2026-11-09 | REG-06 | https://www.perkeso.gov.my HTTP fetch via fn_web_fetch | Status 200 (same portal as REG-05); EIS-specific benefit eligibility and contribution rates not confirmed from landing page | Remains ⚠️ KNOWLEDGE-BASED (EIS rate figures not confirmed) |
| 2026-11-09 | REG-07 | https://www.hrdcorp.gov.my HTTP fetch via fn_web_fetch | Status 200 — "tightened training" announcement dated 22 Oct 2026 still visible; levy rate and exemption criteria not confirmed from landing page | Remains ⚠️ KNOWLEDGE-BASED (levy rate requires targeted navigation) |
| 2026-11-09 | REG-08 | https://www.lhdn.gov.my HTTP fetch via fn_web_fetch | DNS lookup failed (NXDOMAIN) | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-11-09 | REG-09 | https://www.lhdn.gov.my HTTP fetch via fn_web_fetch | DNS lookup failed (NXDOMAIN) | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-11-09 | REG-10 | https://sdk.myinvois.hasil.gov.my HTTP fetch via fn_web_fetch | Status 200 — SDK portal confirmed accessible; API Definition, Release Notes, FAQ sections visible | Remains ✅ VERIFIED (21 Oct 2026; re-confirmed 2026-11-09) |
| 2026-11-09 | REG-11 | https://www.lhdn.gov.my HTTP fetch via fn_web_fetch | DNS lookup failed (NXDOMAIN) — wave schedule source unreachable | Remains ◐ DIRECTIONAL |
| 2026-11-09 | REG-12 | https://www.ssm.com.my HTTP fetch via fn_web_fetch | Status 200 — MBRS, e-CBID, e-Search, Companies (Amendment) Act 2024, LLP (Amendment) Act 2024, AML/CFT, CLRC sections visible; new announcements: SSM Chairman appointment (Dato' Seri Mohd Sayuthi Bakar, effective 1 Oct 2026), late-fee exemption extension to 31 Dec 2026; XBRL requirements and s.68 deadline still not confirmed from homepage | Remains ⚠️ KNOWLEDGE-BASED (MBRS/XBRL filing requirements require targeted navigation) |

**Sweep summary (2026-11-09):** 4 of 12 sources unreachable (REG-01 PDPA, REG-02 AMLA direct, REG-08/09/11 LHDN — DNS NXDOMAIN); 1 source access-denied (REG-04 EPF — HTTP 403); 1 source flaky (REG-03 SST — network error this sweep, was HTTP 200 earlier today); 6 sources reachable (REG-02 via BNM portal, REG-05/06/07/10/12). **No status flag changes.** Only REG-10 remains ✅ VERIFIED. All filing-path features remain gated. Next sweep due: 2026-11-16 (weekly cadence).

---

## Verification Attempt — 2026-10-25 (Heartbeat — weekly cadence sweep)

All 12 REG rows re-checked against official sources per the verification cadence convention (last sweep 2026-11-09; weekly cadence).

| Date | Row | Method | Result | Status after attempt |
| --- | --- | --- | --- | --- |
| 2026-10-25 | REG-01 | www.pdpa.gov.my HTTP fetch via fn_web_fetch | DNS lookup failed (NXDOMAIN) | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 | REG-02 | www.amla.gov.my HTTP fetch via fn_web_fetch | DNS lookup failed (NXDOMAIN); https://www.bnm.gov.my/web/amlcft re-confirmed HTTP 200 — AML/CFT regime, CDD, sanctions, record-keeping, reporting, penalties, FAQs sections visible | Remains ◐ DIRECTIONAL (BNM competent-authority portal re-confirmed reachable) |
| 2026-10-25 | REG-03 | https://www.mysst.customs.gov.my HTTP fetch via fn_web_fetch | fetch failed (network error) — consistent with v1.0 flakiness; row stays ◐ DIRECTIONAL, no silent downgrade, attempt logged | Remains ◐ DIRECTIONAL (source flakiness noted; numeric rates still require targeted navigation) |
| 2026-10-25 | REG-04 | https://www.kwsp.gov.my HTTP fetch via fn_web_fetch | HTTP 403 Forbidden (consistent with all prior sweeps) | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 | REG-05 | https://www.perkeso.gov.my HTTP fetch via fn_web_fetch | Status 200 — portal lists program categories (LINDUNG, PRIHATIN, ASSIST), mandatory registration notices for Malaysian citizens/foreigners/domestic workers/self-employed, "Belanjawan 2027", "LINDUNG 24 Jam", "Panduan Portal ASSIST", "Program Pemandu Sihat & Selamat"; contribution rate tables still not visible on landing page | Remains ⚠️ KNOWLEDGE-BASED (rate tables require targeted navigation) |
| 2026-10-25 | REG-06 | https://www.perkeso.gov.my HTTP fetch via fn_web_fetch | Status 200 (same portal as REG-05); EIS-specific benefit eligibility and contribution rates not confirmed from landing page | Remains ⚠️ KNOWLEDGE-BASED (EIS rate figures not confirmed) |
| 2026-10-25 | REG-07 | https://www.hrdcorp.gov.my HTTP fetch via fn_web_fetch | Status 200 — "tightened training" announcement dated 22 Oct 2026 still visible; levy rate and exemption criteria not confirmed from landing page | Remains ⚠️ KNOWLEDGE-BASED (levy rate requires targeted navigation) |
| 2026-10-25 | REG-08 | https://www.lhdn.gov.my HTTP fetch via fn_web_fetch | DNS lookup failed (NXDOMAIN) | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 | REG-09 | https://www.lhdn.gov.my HTTP fetch via fn_web_fetch | DNS lookup failed (NXDOMAIN) | Remains ⚠️ KNOWLEDGE-BASED |
| 2026-10-25 | REG-10 | https://sdk.myinvois.hasil.gov.my HTTP fetch via fn_web_fetch | Status 200 — SDK portal confirmed accessible; API Definition, Release Notes, FAQ sections visible | Remains ✅ VERIFIED (21 Oct 2026; re-confirmed 2026-10-25) |
| 2026-10-25 | REG-11 | https://www.lhdn.gov.my HTTP fetch via fn_web_fetch | DNS lookup failed (NXDOMAIN) — wave schedule source unreachable | Remains ◐ DIRECTIONAL |
| 2026-10-25 | REG-12 | https://www.ssm.com.my HTTP fetch via fn_web_fetch | Status 200 — MBRS, e-CBID, e-Search, Companies (Amendment) Act 2024, LLP (Amendment) Act 2024, AML/CFT, CLRC sections visible; new announcements: SSM Chairman appointment (Dato' Seri Mohd Sayuthi Bakar, effective 1 Oct 2026), late-fee exemption extension to 31 Dec 2026; XBRL requirements and s.68 deadline still not confirmed from homepage | Remains ⚠️ KNOWLEDGE-BASED (MBRS/XBRL filing requirements require targeted navigation) |

**Sweep summary (2026-10-25):** 4 of 12 sources unreachable (REG-01 PDPA, REG-02 AMLA direct, REG-08/09/11 LHDN — DNS NXDOMAIN); 1 source access-denied (REG-04 EPF — HTTP 403); 1 source flaky (REG-03 SST — network error, consistent with v1.0); 6 sources reachable (REG-02 via BNM portal, REG-05/06/07/10/12). **No status flag changes.** Only REG-10 remains ✅ VERIFIED. All filing-path features remain gated. Next sweep due: 2026-11-01 (weekly cadence).

---

## Verification Attempt — 2026-10-25 (Heartbeat — REG-02 AMLA follow-up research)

Targeted deep-dive into BNM AML/CFT portal to confirm implementation-critical AMLA values.

| Date | Row | Method | Result | Status after attempt |
| --- | --- | --- | --- | --- |
| 2026-10-25 | REG-02 | BNM AML/CFT portal (https://www.bnm.gov.my/web/amlcft/record-keeping) HTTP fetch via fn_web_fetch | **Confirmed: 6-year retention period** — "The records must be kept for at least 6 years following the date of completion of the transaction or termination of the business relationship or occasional transaction." | Remains ◐ DIRECTIONAL (implementation-critical value confirmed via BNM policy document; official amla.gov.my still DNS unreachable) |
| 2026-10-25 | REG-02 | BNM AML/CFT portal (https://www.bnm.gov.my/web/amlcft/reporting-to-bnm) HTTP fetch via fn_web_fetch | **Confirmed: STR filing within next working day** per s.20 AMLA ("The Compliance Officer must ensure that the STR is submitted within the next working day, from the date the Compliance Officer establishes the suspicion."); **CTR threshold RM25,000** for selected reporting institutions (banking institutions, selected DFIs, Lembaga Tabung Haji, licensed casino); **Reporting institution categories** confirmed | Remains ◐ DIRECTIONAL (implementation-critical values confirmed via BNM policy document; official amla.gov.my still DNS unreachable) |

**Summary:** REG-02 updated with confirmed implementation-critical values from BNM AML/CFT portal (competent authority under AMLA). Record retention = 6 years (resolves design-doc conflict: audit-log-design.md §3.1 states 7 years, audit-log-db-notes.md §6 states 5 years; BNM confirms 6 years). STR filing = next working day per s.20 AMLA. CTR threshold = RM25,000 for selected RIs. Reporting institution categories confirmed. Status remains ◐ DIRECTIONAL pending amla.gov.my direct verification. Next sweep due: 2026-11-01 (weekly cadence).
