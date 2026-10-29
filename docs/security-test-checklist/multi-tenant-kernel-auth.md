# Multi-tenant Kernel & Auth — Security Test Checklist

**Task:** KB-018
**Slice:** SL-MVKTMUJW-000Y-KHRJ (Multi-tenant Kernel & Authentication)
**Created:** 2026-10-24
**Status:** Draft — Pending QA Lead Review

---

## 1. Executive Summary

This document defines the security test checklist for the Multi-tenant Kernel & Authentication slice. It covers token replay, clock skew, claim injection, RLS bypass attempts, and other security-critical test scenarios.

---

## 2. Token Security Tests

### 2.1 Token Replay Prevention

| Test ID | Test Name | Steps | Expected Result | Status |
|---------|-----------|-------|-----------------|--------|
| SEC-TOKEN-001 | Single-use token replay | 1. Authenticate with valid token<br>2. Revoke token<br>3. Attempt to reuse token | Token rejected after revocation | ☐ |
| SEC-TOKEN-002 | Expired token replay | 1. Wait for token to expire<br>2. Attempt to use expired token | Token rejected with 401 | ☐ |
| SEC-TOKEN-003 | Token from different user | 1. Obtain token for user A<br>2. Use token to access user B's data | Access denied, token valid but no authorization | ☐ |
| SEC-TOKEN-004 | Token from different tenant | 1. Obtain token for tenant A<br>2. Use token to access tenant B's data | Access denied, RLS enforced | ☐ |
| SEC-TOKEN-005 | Token with modified payload | 1. Obtain valid token<br>2. Modify payload (base64 decode, edit, re-encode)<br>3. Attempt to use modified token | Signature validation fails, token rejected | ☐ |
| SEC-TOKEN-006 | Token with modified signature | 1. Obtain valid token<br>2. Modify signature<br>3. Attempt to use modified token | Signature validation fails, token rejected | ☐ |
| SEC-TOKEN-007 | Token with removed signature | 1. Obtain valid token<br>2. Remove signature segment<br>3. Attempt to use token | Token format invalid, rejected | ☐ |
| SEC-TOKEN-008 | Token with algorithm confusion | 1. Obtain RS256 token<br>2. Change header to HS256<br>3. Attempt to use modified token | Algorithm mismatch, token rejected | ☐ |
| SEC-TOKEN-009 | Token with none algorithm | 1. Obtain valid token<br>2. Change header algorithm to "none"<br>3. Remove signature<br>4. Attempt to use token | Algorithm "none" rejected | ☐ |
| SEC-TOKEN-010 | Token replay across sessions | 1. Obtain token in session A<br>2. Use token in session B<br>3. Verify token is bound to session | Token either session-bound or properly stateless | ☐ |

### 2.2 Clock Skew Tolerance

| Test ID | Test Name | Steps | Expected Result | Status |
|---------|-----------|-------|-----------------|--------|
| SEC-CLOCK-001 | Token 5 minutes in future | 1. Generate token with nbf 5 min in future<br>2. Attempt to use token | Token accepted (within skew tolerance) | ☐ |
| SEC-CLOCK-002 | Token 10 minutes in future | 1. Generate token with nbf 10 min in future<br>2. Attempt to use token | Token rejected (outside skew tolerance) | ☐ |
| SEC-CLOCK-003 | Token 5 minutes expired | 1. Generate token with exp 5 min ago<br>2. Attempt to use token | Token accepted (within skew tolerance) | ☐ |
| SEC-CLOCK-004 | Token 10 minutes expired | 1. Generate token with exp 10 min ago<br>2. Attempt to use token | Token rejected (outside skew tolerance) | ☐ |
| SEC-CLOCK-005 | Server clock skew simulation | 1. Adjust server clock by +5 min<br>2. Validate tokens | Tokens validated correctly with skew compensation | ☐ |
| SEC-CLOCK-006 | Client clock skew simulation | 1. Adjust client clock by +5 min<br>2. Generate and validate token | Token validation accounts for client skew | ☐ |

---

## 3. Claim Injection Tests

### 3.1 Claim Tampering

| Test ID | Test Name | Steps | Expected Result | Status |
|---------|-----------|-------|-----------------|--------|
| SEC-CLAIM-001 | Add admin role claim | 1. Obtain regular user token<br>2. Inject `role: admin` claim<br>3. Attempt admin operation | Claim ignored or signature fails, access denied | ☐ |
| SEC-CLAIM-002 | Add MFA claim | 1. Obtain token without MFA<br>2. Inject MFA claim<br>3. Attempt MFA-required operation | Claim ignored or signature fails, access denied | ☐ |
| SEC-CLAIM-003 | Modify tenant_id claim | 1. Obtain token for tenant A<br>2. Change tenant_id to tenant B<br>3. Access tenant B data | Claim ignored or signature fails, access denied | ☐ |
| SEC-CLAIM-004 | Remove required claim | 1. Obtain valid token<br>2. Remove `sub` claim<br>3. Attempt to use token | Token rejected (missing required claim) | ☐ |
| SEC-CLAIM-005 | Duplicate claims | 1. Obtain valid token<br>2. Add duplicate `role` claims<br>3. Attempt to use token | Token rejected or first claim used | ☐ |
| SEC-CLAIM-006 | Claim type confusion | 1. Obtain token with `role: "user"`<br>2. Modify to `role: ["user", "admin"]`<br>3. Attempt admin operation | Type validation fails, access denied | ☐ |
| SEC-CLAIM-007 | Null claim injection | 1. Obtain valid token<br>2. Set `tenant_id: null`<br>3. Attempt data access | Null claim rejected, fail-closed | ☐ |
| SEC-CLAIM-008 | Empty string claim | 1. Obtain valid token<br>2. Set `tenant_id: ""`<br>3. Attempt data access | Empty claim rejected, fail-closed | ☐ |

### 3.2 JWT Structure Attacks

| Test ID | Test Name | Steps | Expected Result | Status |
|---------|-----------|-------|-----------------|--------|
| SEC-JWT-001 | JWT with extra segments | 1. Obtain valid JWT (3 segments)<br>2. Add extra segment<br>3. Attempt to parse | Token format invalid, rejected | ☐ |
| SEC-JWT-002 | JWT with missing segments | 1. Obtain valid JWT<br>2. Remove signature segment<br>3. Attempt to parse | Token format invalid, rejected | ☐ |
| SEC-JWT-003 | JWT with invalid base64 | 1. Obtain valid JWT<br>2. Corrupt base64 in payload<br>3. Attempt to parse | Base64 decode fails, rejected | ☐ |
| SEC-JWT-004 | JWT with unicode in header | 1. Create JWT with unicode in header<br>2. Attempt to parse | Header parsing handles unicode safely | ☐ |
| SEC-JWT-005 | JWT with very large payload | 1. Create JWT with 1MB payload<br>2. Attempt to validate | Payload size limit enforced, rejected | ☐ |
| SEC-JWT-006 | JWT with nested JSON | 1. Create JWT with deeply nested JSON<br>2. Attempt to parse | JSON parsing handles nesting safely | ☐ |

---

## 4. RLS Bypass Tests

### 4.1 Direct Database Access

| Test ID | Test Name | Steps | Expected Result | Status |
|---------|-----------|-------|-----------------|--------|
| SEC-RLS-001 | Superuser bypass attempt | 1. Connect as superuser<br>2. Query tenant-scoped table<br>3. Verify RLS still enforced | RLS bypassed for superuser (expected), but app never uses superuser | ☐ |
| SEC-RLS-002 | BYPASSRLS role check | 1. Verify app role has no BYPASSRLS<br>2. Query as app role | App role cannot bypass RLS | ☐ |
| SEC-RLS-003 | Table owner bypass | 1. Create table owned by app role<br>2. Enable FORCE RLS<br>3. Query as app role | FORCE RLS prevents owner bypass | ☐ |
| SEC-RLS-004 | RLS disabled check | 1. Check RLS enabled on all tenant-scoped tables<br>2. Verify no tables have RLS disabled | All tenant-scoped tables have RLS enabled | ☐ |
| SEC-RLS-005 | RLS not forced check | 1. Check RLS forced on all tenant-scoped tables<br>2. Verify no tables have RLS not forced | All tenant-scoped tables have FORCE RLS | ☐ |
| SEC-RLS-006 | Policy missing check | 1. Check policies on all tenant-scoped tables<br>2. Verify each table has tenant isolation policy | All tenant-scoped tables have isolation policy | ☐ |
| SEC-RLS-007 | Raw SQL injection | 1. Inject raw SQL via query parameter<br>2. Attempt to disable RLS<br>3. Execute query | Raw SQL execution blocked or RLS still enforced | ☐ |
| SEC-RLS-008 | ORM escape | 1. Use ORM raw query escape hatch<br>2. Attempt cross-tenant query | Raw query still subject to RLS | ☐ |

### 4.2 Tenant Context Manipulation

| Test ID | Test Name | Steps | Expected Result | Status |
|---------|-----------|-------|-----------------|--------|
| SEC-CONTEXT-001 | No tenant context | 1. Execute query without setting tenant context<br>2. Verify result | Zero rows returned (fail-closed) | ☐ |
| SEC-CONTEXT-002 | NULL tenant context | 1. Set `app.tenant_id = NULL`<br>2. Execute query | Zero rows returned (fail-closed) | ☐ |
| SEC-CONTEXT-003 | Empty string tenant context | 1. Set `app.tenant_id = ''`<br>2. Execute query | Type cast fails or zero rows returned | ☐ |
| SEC-CONTEXT-004 | Invalid UUID tenant context | 1. Set `app.tenant_id = 'not-a-uuid'`<br>2. Execute query | Type cast fails, query rejected | ☐ |
| SEC-CONTEXT-005 | Cross-tenant context | 1. Set tenant context to tenant A<br>2. Attempt to query tenant B data | Zero tenant B rows returned | ☐ |
| SEC-CONTEXT-006 | Context leakage between requests | 1. Set tenant context for request A<br>2. Execute request B without context<br>3. Verify context not leaked | Request B has no tenant context, returns zero rows | ☐ |
| SEC-CONTEXT-007 | Context leakage in connection pool | 1. Use connection for tenant A<br>2. Return connection to pool<br>3. Use same connection for tenant B<br>4. Verify context reset | Connection properly reset, no leakage | ☐ |
| SEC-CONTEXT-008 | SET LOCAL vs SET | 1. Use `SET` instead of `SET LOCAL`<br>2. Verify context persists beyond transaction | Context properly scoped to transaction only | ☐ |
| SEC-CONTEXT-009 | Multiple tenant contexts in transaction | 1. Set tenant context twice in same transaction<br>2. Execute query | Last context wins, no ambiguity | ☐ |
| SEC-CONTEXT-010 | Context in nested transaction | 1. Set tenant context in outer transaction<br>2. Begin nested transaction<br>3. Execute query | Context inherited in nested transaction | ☐ |

---

## 5. Authentication Security Tests

### 5.1 Credential Security

| Test ID | Test Name | Steps | Expected Result | Status |
|---------|-----------|-------|-----------------|--------|
| SEC-AUTH-001 | Password in logs | 1. Attempt authentication<br>2. Check application logs<br>3. Verify password not logged | Password not present in logs | ☐ |
| SEC-AUTH-002 | Password in error messages | 1. Cause authentication error<br>2. Check error message<br>3. Verify password not revealed | Error message generic, no password info | ☐ |
| SEC-AUTH-003 | Password in URL | 1. Attempt to include password in URL<br>2. Verify rejected or stripped | Password in URL rejected or ignored | ☐ |
| SEC-AUTH-004 | Credential storage | 1. Check database for stored credentials<br>2. Verify passwords hashed | Passwords hashed with bcrypt/argon2 | ☐ |
| SEC-AUTH-005 | Hash strength | 1. Check password hash configuration<br>2. Verify cost factor >= 12 | Hash cost factor meets minimum | ☐ |
| SEC-AUTH-006 | Credential transmission | 1. Capture authentication request<br>2. Verify TLS used | TLS 1.2+ enforced | ☐ |

### 5.2 Session Security

| Test ID | Test Name | Steps | Expected Result | Status |
|---------|-----------|-------|-----------------|--------|
| SEC-SESSION-001 | Session fixation | 1. Obtain session ID before auth<br>2. Authenticate<br>3. Verify session ID changed | Session ID regenerated after auth | ☐ |
| SEC-SESSION-002 | Session timeout | 1. Authenticate<br>2. Wait for session timeout<br>3. Attempt to use session | Session expired, re-auth required | ☐ |
| SEC-SESSION-003 | Concurrent session limit | 1. Authenticate from multiple devices<br>2. Exceed session limit<br>3. Verify oldest session invalidated | Oldest session invalidated | ☐ |
| SEC-SESSION-004 | Session hijacking | 1. Obtain valid session<br>2. Use session from different IP<br>3. Verify session still valid or flagged | Session either IP-bound or flagged for review | ☐ |
| SEC-SESSION-005 | Session revocation | 1. Authenticate<br>2. Revoke session<br>3. Attempt to use revoked session | Session rejected | ☐ |
| SEC-SESSION-006 | Logout all sessions | 1. Authenticate from multiple devices<br>2. Logout all sessions<br>3. Verify all sessions invalidated | All sessions invalidated | ☐ |

---

## 6. MFA Security Tests

### 6.1 MFA Enforcement

| Test ID | Test Name | Steps | Expected Result | Status |
|---------|-----------|-------|-----------------|--------|
| SEC-MFA-001 | MFA required policy | 1. Set MFA policy to required<br>2. Attempt login without MFA<br>3. Verify rejected | Login rejected, MFA required | ☐ |
| SEC-MFA-002 | MFA optional policy | 1. Set MFA policy to optional<br>2. Attempt login without MFA<br>3. Verify accepted | Login accepted, warning shown | ☐ |
| SEC-MFA-003 | MFA bypass attempt | 1. Attempt to skip MFA step<br>2. Verify rejected | MFA step cannot be skipped | ☐ |
| SEC-MFA-004 | MFA code replay | 1. Use valid MFA code<br>2. Reuse same MFA code<br>3. Verify rejected | MFA code single-use only | ☐ |
| SEC-MFA-005 | MFA code brute force | 1. Attempt multiple MFA codes<br>2. Verify rate limiting | Rate limited after N attempts | ☐ |
| SEC-MFA-006 | MFA code timing attack | 1. Measure response time for valid vs invalid codes<br>2. Verify timing consistent | Response time does not leak validity | ☐ |

---

## 7. Audit Log Security Tests

### 7.1 Audit Log Integrity

| Test ID | Test Name | Steps | Expected Result | Status |
|---------|-----------|-------|-----------------|--------|
| SEC-AUDIT-001 | Audit log tampering | 1. Modify audit log record<br>2. Verify chain hash broken | Chain verification fails | ☐ |
| SEC-AUDIT-002 | Audit log deletion | 1. Attempt to DELETE from audit_log<br>2. Verify rejected | DELETE rejected by RLS/constraint | ☐ |
| SEC-AUDIT-003 | Audit log update | 1. Attempt to UPDATE audit_log<br>2. Verify rejected | UPDATE rejected by RLS/constraint | ☐ |
| SEC-AUDIT-004 | Audit log insertion | 1. Insert valid audit record<br>2. Verify chain hash computed | Chain hash correctly computed | ☐ |
| SEC-AUDIT-005 | Audit log tenant isolation | 1. Query audit_log with tenant A context<br>2. Verify zero tenant B rows | Tenant isolation enforced | ☐ |
| SEC-AUDIT-006 | Meta-audit recording | 1. Query audit_log<br>2. Verify meta-audit record created | Meta-audit entry present | ☐ |

### 7.2 Audit Log Redaction

| Test ID | Test Name | Steps | Expected Result | Status |
|---------|-----------|-------|-----------------|--------|
| SEC-REDACT-001 | Password redaction | 1. Trigger audit event with password<br>2. Verify password not in audit log | Password redacted | ☐ |
| SEC-REDACT-002 | Token redaction | 1. Trigger audit event with auth token<br>2. Verify token not in audit log | Token redacted | ☐ |
| SEC-REDACT-003 | Bank account redaction | 1. Access bank credential<br>2. Verify full account number not in audit log | Account number redacted/masked | ☐ |
| SEC-REDACT-004 | NRIC redaction | 1. Access personal data with NRIC<br>2. Verify NRIC not in audit log | NRIC redacted | ☐ |
| SEC-REDACT-005 | Certificate redaction | 1. Use certificate for auth<br>2. Verify certificate not in audit log | Certificate redacted | ☐ |

---

## 8. Rate Limiting Security Tests

### 8.1 Rate Limit Enforcement

| Test ID | Test Name | Steps | Expected Result | Status |
|---------|-----------|-------|-----------------|--------|
| SEC-RATE-001 | Authentication rate limit | 1. Send N+1 auth requests<br>2. Verify (N+1)th request rate-limited | 429 Too Many Requests | ☐ |
| SEC-RATE-002 | MFA rate limit | 1. Send N+1 MFA verification requests<br>2. Verify (N+1)th request rate-limited | 429 Too Many Requests | ☐ |
| SEC-RATE-003 | Password reset rate limit | 1. Send N+1 password reset requests<br>2. Verify (N+1)th request rate-limited | 429 Too Many Requests | ☐ |
| SEC-RATE-004 | Rate limit bypass via IP rotation | 1. Send requests from multiple IPs<br>2. Verify rate limiting still effective | Rate limiting per-IP or per-user | ☐ |
| SEC-RATE-005 | Rate limit bypass via user agent | 1. Send requests with different user agents<br>2. Verify rate limiting still effective | Rate limiting not UA-dependent | ☐ |
| SEC-RATE-006 | Rate limit headers | 1. Send request within limit<br>2. Verify X-RateLimit headers present | Headers present with correct values | ☐ |

---

## 9. User Enumeration Prevention

### 9.1 Enumeration Resistance

| Test ID | Test Name | Steps | Expected Result | Status |
|---------|-----------|-------|-----------------|--------|
| SEC-ENUM-001 | Invalid user error message | 1. Attempt login with non-existent user<br>2. Check error message | Generic error, no "user not found" | ☐ |
| SEC-ENUM-002 | Invalid password error message | 1. Attempt login with valid user, wrong password<br>2. Check error message | Same generic error as invalid user | ☐ |
| SEC-ENUM-003 | Password reset enumeration | 1. Request password reset for non-existent user<br>2. Check response | Generic response, no "user not found" | ☐ |
| SEC-ENUM-004 | Timing-based enumeration | 1. Measure response time for valid vs invalid user<br>2. Verify timing consistent | Response time does not leak user existence | ☐ |
| SEC-ENUM-005 | MFA enumeration | 1. Request MFA for non-existent user<br>2. Check response | Generic response | ☐ |

---

## 10. Security Test Execution

### 10.1 Pre-Release Security Gate

All security tests must pass before release:

```bash
pnpm run test:security:auth
```

### 10.2 Security Test Report

Generate security test report:

```bash
pnpm run test:security:report
```

Report includes:
- Pass/fail status for each test
- Evidence of test execution
- Remediation steps for failures
- Sign-off from security engineer

### 10.3 Periodic Security Audits

- **Monthly:** Run full security test suite
- **Quarterly:** External penetration test
- **Annually:** Comprehensive security audit

---

## 11. Security Test Checklist Summary

| Category | Tests | Required Pass | Actual Pass | Status |
|----------|-------|---------------|-------------|--------|
| Token Security | 10 | 10 | 0 | ☐ Pending |
| Clock Skew | 6 | 6 | 0 | ☐ Pending |
| Claim Injection | 14 | 14 | 0 | ☐ Pending |
| RLS Bypass | 18 | 18 | 0 | ☐ Pending |
| Authentication | 11 | 11 | 0 | ☐ Pending |
| MFA | 6 | 6 | 0 | ☐ Pending |
| Audit Log | 11 | 11 | 0 | ☐ Pending |
| Rate Limiting | 6 | 6 | 0 | ☐ Pending |
| User Enumeration | 5 | 5 | 0 | ☐ Pending |
| **Total** | **87** | **87** | **0** | **☐ Pending** |

---

*End of security test checklist document.*
