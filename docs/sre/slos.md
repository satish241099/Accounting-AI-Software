# Service Level Objectives — Malaysia Accounting SaaS

## Committed SLOs

| SLO | Target | Measurement Window | Error Definition |
|-----|--------|-------------------|------------------|
| **e-Invois API uptime** | **99.5%** | 30 days rolling | 5xx response / timeout > 30s / failed authentication (invalid/missing token, expired 60-min token, certificate validation failure) |
| **Auth uptime** | **99.9%** | 30 days rolling | 5xx response / timeout > 30s / failed auth (invalid/missing token, expired 60-min token, certificate validation failure) |
| **General API uptime** | **99.5%** | 30 days rolling | 5xx response / timeout > 30s / failed authentication |

## Measurement Definition

- **Window:** 30-day rolling window (i.e., for any given day, availability is computed over the prior 30 consecutive days).
- **Numerator:** Successful requests = requests where no error definition condition is met.
- **Denominator:** Total requests = all requests matching the service boundary (excluding excluded windows).
- **Availability = (Successful / Total) × 100**, reported as a percentage to one decimal place.

## Error Definitions per Service

### e-Invois API

- **5xx response:** Any HTTP 500–599 response from the e-Invois API gateway.
- **Timeout:** Request not completing within 30 seconds from the client's perspective.
- **Failed authentication:**
  - Invalid or missing JWT bearer token.
  - Expired 60‑minute token (MyInvois SDK enforces a hard 60‑minute expiry; any request with a token older than issuance time is rejected).
  - Certificate validation failure (SHA-256 `documentHash` generation requires a valid CA‑issued digital certificate; certificate chain validation errors count as auth failures).
- **Exclusion windows:** Maintenance/maintenance‑mode windows published by LHDN for e-Invois system upgrades are excluded from the availability calculation. These windows are published at least 48 hours in advance via the MyInvois developer portal. During excluded windows, requests are not counted in the denominator.

### Auth

- **5xx response:** Any HTTP 500–599 response from the auth service.
- **Timeout:** Request not completing within 30 seconds.
- **Failed authentication:** Same conditions as e-Invois API (invalid/missing token, expired 60‑min token, certificate validation failure), since auth is the gateway for all services.

### General API

- **5xx response:** Any HTTP 500–599 response from any API route not classified as e‑Invois or auth.
- **Timeout:** Request not completing within 30 seconds.
- **Failed authentication:** Invalid or missing bearer token, expired 60‑minute token.

## MyInvois API Constraints (Referenced)

- **Token expiry:** 60‑minute hard expiry on all OAuth2 client‑credentials tokens. Tokens must be refreshed before expiry; there is no grace period.
- **Document size limit:** 300 KB maximum payload for e-Invois document submission. Requests exceeding this limit are rejected with a 413 Payload Too Large error and do not count as availability failures.
- **documentHash:** SHA‑256 hash of the canonical document representation. Generation must use a CA‑issued digital certificate. Certificate validation failures count as authentication errors.
- **Regulatory maintenance windows:** LHDN publishes e-Invois maintenance schedules at least 48 hours in advance. These are the only excluded windows for the e‑Invois SLO.

## SLO Availability Calculation Example

```
e-Invois API availability over 30 days:
  Total requests (excluding excluded windows): 10 000
  Failed requests (5xx + timeouts + auth failures): 48
  Availability = (10 000 − 48) / 10 000 × 100 = 99.52% → committed target 99.5%
```

## References

- MyInvois SDK facts: 60‑minute tokens, 300 KB limit, SHA‑256 `documentHash`
- LHDN regulatory maintenance windows — published at least 48h in advance
- ACCO-012 SLO baseline (existing audit‑log alert references)