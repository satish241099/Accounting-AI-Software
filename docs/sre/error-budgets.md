# Error Budgets & Burn-Rate Alerting — Malaysia Accounting SaaS

## Monthly Error Budget per SLO

| SLO | Target Availability | Monthly Downtime Budget | Daily Equivalent |
|-----|---------------------|------------------------|-----------------|
| e-Invois API | 99.5% | **3.6 hours** (216 minutes) | 7.2 minutes |
| Auth | 99.9% | **43.8 minutes** | 0.92 minutes (55.2 seconds) |
| General API | 99.5% | **3.6 hours** (216 minutes) | 7.2 minutes |

### Calculation Method

- **30‑day month = 43 200 minutes** (30 × 24 × 60).
- **Budget = (1 − availability%) × 43 200 minutes**.
  - 99.5% → (1 − 0.995) × 43 200 = 0.005 × 43 200 = **216 minutes = 3.6 hours**.
  - 99.9% → (1 − 0.999) × 43 200 = 0.001 × 43 200 = **43.8 minutes**.

## Burn-Rate Alert Thresholds

| Threshold | Burn Rate | Action | Alert Route |
|-----------|-----------|--------|-------------|
| **2x** | Current burn rate ≥ 2 × budget‑consumption rate | On‑call SRE notification; review release eligibility | SRE on-call channel (Slack/PagerDuty) |
| **5x** | Current burn rate ≥ 5 × budget‑consumption rate | Immediate on‑call escalation; release freeze evaluated | P1 alert to SRE lead and engineering manager |

### Burn‑Rate Calculation

```
burn_rate = (error_budget_consumed_this_period) / (error_budget_total)
           = (downtime_observed / downtime_budget) / (time_elapsed / total_window)
```

- **Budget‑consumption rate** = fraction of the monthly budget burned so far, normalized by the elapsed fraction of the 30‑day window.
- **Example:** After 15 days, if 108 minutes of e‑Invois downtime have been observed:
  - Budget consumed = 108 / 216 = 0.5 (50% of monthly budget used).
  - Elapsed fraction = 15 / 30 = 0.5 (half the window gone).
  - Burn rate = 0.5 / 0.5 = 1.0 (on track).
  - If 216 minutes observed in 15 days: burn rate = 1.0 / 0.5 = **2x** → SRE notification.

## Error Budget Consumption Rules

1. **Budget tracks 5xx responses, timeouts > 30s, and failed authentications** per the SLO error definitions (see `docs/sre/slos.md`).
2. **Excluded maintenance windows are not counted** against the error budget (per SLO definition).
3. **Budget resets at the start of each new 30‑day rolling window** — consumption is not cumulative across windows, but the rolling nature means overlapping windows share the budget.
4. **Release freeze condition:** A release is blocked when the **current burn rate ≥ 1x** (budget fully consumed for the elapsed window) AND the release would add measurable additional load (e.g., new endpoint, increased traffic). At 2x, releases require SRE approval; at 5x, all non‑critical releases are frozen until burn rate abates.
5. **Error budget recovery:** Once the observed error rate drops below the budget‑consumption rate, the budget is considered recovered and releases may proceed under standard rules.

## Release Freeze Conditions

| Burn Rate | Release Freeze |
|-----------|----------------|
| **< 1x** | No freeze. Proceed with standard release gate. |
| **≥ 1x and < 2x** | Release requires SRE sign‑off; risk assessment required. |
| **≥ 2x** | Release blocked unless rollback of recent change is the only action. SRE on-call must approve. |
| **≥ 5x** | All non‑critical releases frozen immediately. Critical security/f compliance releases require SRE lead + engineering manager approval. |

## Alert Routing

- **2x threshold:** SRE on‑call receives notification via Slack/PagerDuty with burn rate value, SLO target, elapsed time, and budget consumed. No auto‑block; human decision on release eligibility.
- **5x threshold:** P1 alert to SRE lead and engineering manager. Automatic evaluation of release freeze; all non‑critical deployment pipelines paused until burn rate falls below 2x.

## Sustaining Error Budget Health

- **Daily monitoring:** SRE team reviews burn rate each morning as part of the shift handoff.
- **Weekly review:** Error budget trends examined during the weekly SRE sync; patterns of recurring failures are documented and addressed.
- **Post‑mortem trigger:** Any SLO breach (availability < target) triggers a post‑mortem within 72 hours (see `docs/sre/slo-review-process.md`).

## References

- ACCO-012 SLO baseline and existing alert references
- MyInvois API constraints: 60‑minute tokens, 300 KB limit, SHA‑256 `documentHash`
- LHDN regulatory maintenance windows — published at least 48h in advance