# Multi-tenant Kernel & Authentication — Test Strategy and Plan

**Task:** KB-018
**Slice:** SL-MVKTMUJW-000Y-KHRJ (Multi-tenant Kernel & Authentication)
**Mission:** M-MVKLBLEY-0001-XSFU (Establish SRE foundation for Malaysia Accounting SaaS)
**Created:** 2026-10-24
**Status:** Draft — Pending QA Lead Review
**Handoff Target:** QA Lead (agent-34863834)

---

## 1. Executive Summary

This document defines the comprehensive test strategy and plan for the Multi-tenant Kernel & Authentication slice, which is the foundation of the Malaysia Accounting SaaS platform. This slice carries the highest security and compliance risk, requiring rigorous testing across 8 critical features.

### 1.1 Slice Verification Criteria

The slice is considered verified when all of the following are demonstrated:

1. **User can sign in with MFA** — Authentication flow completes with valid MFA claim
2. **User can switch businesses** — Tenant context switching works without re-authentication
3. **User accesses only their data** — RLS policies enforce zero cross-tenant data leakage
4. **Route coverage guard passes** — Public vs authenticated vs tenant-scoped routes are correctly enforced
5. **Revocation effective on next request** — Token/credential revocation takes effect immediately
6. **RLS test proves zero rows without context** — Fail-closed behavior when no tenant context is set
7. **All auth events present in audit log** — Complete audit trail for authentication and authorization events

---

## 2. Feature Coverage Matrix

| Feature ID | Feature Name | Test Type | Owner | Status |
|------------|--------------|-----------|-------|--------|
| F-MVKTMUKF-0010-L4YE | Entra External ID Integration | Unit | QA Lead | Planned |
| F-MVKTMUMQ-0013-YF80 | MFA Validation | Unit | QA Lead | Planned |
| F-MVKTMUNQ-0015-S6VS | Membership Lifecycle | Unit + Integration | QA Lead | Planned |
| F-MVKTMUPC-0017-6UPF | Role Permissions Matrix | Unit | QA Lead | Planned |
| F-MVKTMUQ8-0019-1H2U | Row-Level Security | Integration | QA Lead | Planned |
| F-MVKTMUR9-001B-2YS5 | Route Coverage Guard | Integration | QA Lead | Planned |
| F-MVKTMUSS-001D-92EB | Audit Events | Integration | QA Lead | Planned |
| F-MVKTMUTT-001F-JY4B | Abuse Protection | Integration | QA Lead | Planned |

---

## 3. Test Plan by Feature

### 3.1 F-MVKTMUKF-0010-L4YE — Entra External ID Integration

**Objective:** Validate secure integration with Microsoft Entra External ID for authentication.

#### Unit Test Cases

| Test ID | Test Name | Acceptance Criteria | Verification Method |
|---------|-----------|---------------------|---------------------|
| UT-ENTRA-001 | Signature Verification | Valid JWT signatures are accepted; invalid signatures are rejected | Mock signing keys, verify signature validation logic |
| UT-ENTRA-002 | Key Caching | Signing keys are cached for TTL duration; cache invalidation works on key rotation | Verify cache hit/miss behavior, TTL expiration |
| UT-ENTRA-003 | Key Rotation | New signing keys are fetched automatically; old keys are rejected after rotation | Simulate key rotation, verify seamless transition |
| UT-ENTRA-004 | Claim Validation — Issuer | Only tokens from configured issuer are accepted | Test with valid/invalid issuer claims |
| UT-ENTRA-005 | Claim Validation — Audience | Only tokens with matching audience are accepted | Test with valid/invalid audience claims |
| UT-ENTRA-006 | Claim Validation — Expiry | Expired tokens are rejected; not-yet-valid tokens are rejected | Test with expired/nbf-future tokens |
| UT-ENTRA-007 | Claim Validation — Required Claims | Missing required claims cause rejection | Test with tokens missing `sub`, `tid`, `email` |
| UT-ENTRA-008 | Clock Skew Tolerance | Valid tokens within configured clock skew (±5 min) are accepted | Test with tokens at skew boundaries |

#### Test Data Requirements

- Mock Entra signing keys (RSA-256, ECDSA)
- Valid JWT tokens with various claim combinations
- Expired/not-yet-valid tokens
- Tokens with tampered signatures

#### Dependencies

- Mock JWKS endpoint for key fetching
- Token generation utility for test fixtures

---

### 3.2 F-MVKTMUMQ-0013-YF80 — MFA Validation

**Objective:** Validate conditional MFA enforcement and generic error responses.

#### Unit Test Cases

| Test ID | Test Name | Acceptance Criteria | Verification Method |
|---------|-----------|---------------------|---------------------|
| UT-MFA-001 | MFA Claim Present — Valid | User with valid MFA claim is authenticated | Mock MFA claim, verify auth success |
| UT-MFA-002 | MFA Claim Present — Invalid | User with invalid MFA claim is rejected | Mock invalid MFA claim, verify rejection |
| UT-MFA-003 | MFA Claim Missing — Policy Requires | User without MFA claim is rejected when policy requires MFA | Test with missing MFA claim, policy=required |
| UT-MFA-004 | MFA Claim Missing — Policy Optional | User without MFA claim is accepted when policy is optional | Test with missing MFA claim, policy=optional |
| UT-MFA-005 | Generic Error — No User Enumeration | Error messages do not reveal whether user exists | Verify error messages are identical for invalid user/invalid MFA |
| UT-MFA-006 | Conditional MFA — High Risk | MFA is required for high-risk operations regardless of session state | Test high-risk operation without MFA, verify rejection |
| UT-MFA-007 | Conditional MFA — Low Risk | MFA is not required for low-risk operations | Test low-risk operation without MFA, verify success |

#### Test Data Requirements

- User fixtures with MFA enabled/disabled
- MFA claim variants (valid, invalid, missing, expired)
- Risk level configurations (high/low risk operations)

#### Security Considerations

- Error messages must be generic: "Authentication failed" — never "User not found" or "Invalid MFA code"
- Rate limiting must apply to MFA verification attempts
- MFA bypass attempts must be logged to audit trail

---

### 3.3 F-MVKTMUNQ-0015-S6VS — Membership Lifecycle

**Objective:** Validate tenant membership operations including invite, acceptance, removal, and ownership transfer.

#### Unit Test Cases

| Test ID | Test Name | Acceptance Criteria | Verification Method |
|---------|-----------|---------------------|---------------------|
| UT-MEMBER-001 | Invite Flow — Valid Email | Invitation is sent to valid email address | Verify invitation record created, email sent |
| UT-MEMBER-002 | Invite Flow — Invalid Email | Invitation fails for invalid email format | Verify validation error, no invitation created |
| UT-MEMBER-003 | Invite Flow — Duplicate Email | Duplicate invitation to same email updates existing invitation | Verify existing invitation updated, no duplicate |
| UT-MEMBER-004 | Acceptance — Valid Token | Invitation acceptance with valid token creates membership | Verify membership record created, invitation consumed |
| UT-MEMBER-005 | Acceptance — Expired Token | Invitation acceptance with expired token fails | Verify rejection, no membership created |
| UT-MEMBER-006 | Acceptance — Wrong Email | Invitation acceptance with mismatched email fails | Verify rejection, no membership created |
| UT-MEMBER-007 | Removal — Member Exists | Member removal succeeds for existing member | Verify membership record deleted/deactivated |
| UT-MEMBER-008 | Removal — Member Not Found | Member removal fails gracefully for non-existent member | Verify no error, idempotent behavior |
| UT-MEMBER-009 | Removal — Last Owner | Removing last owner fails | Verify rejection with specific error |
| UT-MEMBER-010 | Ownership Transfer — Valid | Ownership transfer to existing member succeeds | Verify ownership transferred, previous owner demoted |
| UT-MEMBER-011 | Ownership Transfer — Invalid Target | Ownership transfer to non-member fails | Verify rejection, ownership unchanged |
| UT-MEMBER-012 | Ownership Transfer — Self | Ownership transfer to self is no-op | Verify idempotent success |

#### Integration Test Cases

| Test ID | Test Name | Acceptance Criteria | Verification Method |
|---------|-----------|---------------------|---------------------|
| IT-MEMBER-001 | Invite → Accept → Access Data | Full lifecycle: invited user can access tenant data after acceptance | End-to-end flow test |
| IT-MEMBER-002 | Remove → Revoke Access | Removed user cannot access tenant data on next request | Verify access denied post-removal |
| IT-MEMBER-003 | Ownership Transfer → Admin Access | New owner has full admin access; previous owner has reduced access | Verify permission changes |

#### Test Data Requirements

- Tenant fixtures with various membership states
- Invitation tokens (valid, expired, consumed)
- User fixtures with different roles (owner, admin, member)

---

### 3.4 F-MVKTMUPC-0017-6UPF — Role Permissions Matrix

**Objective:** Validate all permission boundaries and external accountant constraints.

#### Unit Test Cases

| Test ID | Test Name | Acceptance Criteria | Verification Method |
|---------|-----------|---------------------|---------------------|
| UT-PERM-001 | Owner — Full Access | Owner role has all permissions | Verify permission check returns true for all actions |
| UT-PERM-002 | Admin — Administrative Actions | Admin role has administrative permissions but cannot transfer ownership | Verify admin permissions, verify ownership transfer denied |
| UT-PERM-003 | Member — Standard Actions | Member role has standard operational permissions | Verify member permissions |
| UT-PERM-004 | External Accountant — Read-Only | External accountant role has read-only access to financial data | Verify read permissions, verify write denied |
| UT-PERM-005 | External Accountant — No Sensitive Data | External accountant cannot access bank credentials, tax IDs | Verify sensitive data access denied |
| UT-PERM-006 | Permission — Create Invoice | Roles with invoice creation permission can create invoices | Verify permission check |
| UT-PERM-007 | Permission — Delete Invoice | Only specific roles can delete invoices | Verify role-based deletion permission |
| UT-PERM-008 | Permission — View Audit Log | Only compliance/admin roles can view audit logs | Verify audit log access control |
| UT-PERM-009 | Permission Boundary — Cross-Tenant | User cannot have permissions in tenant they don't belong to | Verify cross-tenant permission check fails |
| UT-PERM-010 | Permission Inheritance — Role Hierarchy | Higher roles inherit permissions from lower roles | Verify permission inheritance |

#### Test Data Requirements

- Role fixtures (owner, admin, member, external_accountant)
- Permission matrix definition
- Action-to-permission mappings

---

### 3.5 F-MVKTMUQ8-0019-1H2U — Row-Level Security

**Objective:** Validate per-request transaction isolation and RLS bypass attempts.

#### Integration Test Cases

| Test ID | Test Name | Acceptance Criteria | Verification Method |
|---------|-----------|---------------------|---------------------|
| IT-RLS-001 | Read Isolation — Tenant A Context | SELECT with tenant A context returns only tenant A rows | Query with tenant A context, verify zero tenant B rows |
| IT-RLS-002 | Read Isolation — Tenant B Context | SELECT with tenant B context returns only tenant B rows | Query with tenant B context, verify zero tenant A rows |
| IT-RLS-003 | Write Isolation — INSERT | INSERT with tenant A context cannot stamp tenant B id | Attempt INSERT with tenant B id, verify rejection |
| IT-RLS-004 | Write Isolation — UPDATE | UPDATE with tenant A context cannot modify tenant B rows | Attempt UPDATE on tenant B row, verify 0 rows affected |
| IT-RLS-005 | Write Isolation — DELETE | DELETE with tenant A context cannot delete tenant B rows | Attempt DELETE on tenant B row, verify 0 rows affected |
| IT-RLS-006 | No-Context Read — Fail Closed | SELECT with no tenant context returns zero rows | Query without context, verify empty result |
| IT-RLS-007 | No-Context Write — Fail Closed | INSERT/UPDATE/DELETE with no tenant context fails | Attempt write without context, verify rejection |
| IT-RLS-008 | RLS Bypass — Superuser | Test harness uses `app` role, not superuser | Verify test connection role |
| IT-RLS-009 | RLS Bypass — BYPASSRLS | `app` role does not have BYPASSRLS | Verify role permissions |
| IT-RLS-010 | RLS Bypass — Table Owner | Table owner cannot bypass RLS (FORCE RLS enabled) | Verify FORCE RLS on all tenant-scoped tables |
| IT-RLS-011 | Aggregation Isolation | COUNT/SUM with tenant A context includes only tenant A rows | Verify aggregation scope |
| IT-RLS-012 | JOIN Isolation | JOIN across tenant-scoped tables returns only tenant A relationships | Verify JOIN scope |
| IT-RLS-013 | Session Variable Leak | Tenant context does not leak between pooled connections | Verify RESET after each transaction |
| IT-RLS-014 | Advisory Lock — Concurrent Writes | Concurrent inserts serialize correctly via advisory lock | Verify chain hash integrity under concurrency |

#### Test Data Requirements

- Two tenant fixtures (tenant A, tenant B) with UUIDs
- Seed data in all tenant-scoped tables for both tenants
- `app` role credentials (no superuser, no BYPASSRLS)

#### Dependencies

- PostgreSQL instance with RLS enabled
- Schema migrations applied
- `app` role created with correct permissions

#### Reference

See `docs/testing/tenant-isolation-test-plan.md` (ACCO-041) for detailed RLS test harness specification.

---

### 3.6 F-MVKTMUR9-001B-2YS5 — Route Coverage Guard

**Objective:** Validate public vs authenticated vs tenant-scoped route allow-lists.

#### Integration Test Cases

| Test ID | Test Name | Acceptance Criteria | Verification Method |
|---------|-----------|---------------------|---------------------|
| IT-ROUTE-001 | Public Route — No Auth | Public routes accessible without authentication | Request public route without token, verify 200 |
| IT-ROUTE-002 | Public Route — With Auth | Public routes accessible with authentication | Request public route with token, verify 200 |
| IT-ROUTE-003 | Authenticated Route — No Auth | Authenticated routes reject unauthenticated requests | Request auth route without token, verify 401 |
| IT-ROUTE-004 | Authenticated Route — Valid Auth | Authenticated routes accept valid authentication | Request auth route with valid token, verify 200 |
| IT-ROUTE-005 | Authenticated Route — Invalid Auth | Authenticated routes reject invalid authentication | Request auth route with invalid token, verify 401 |
| IT-ROUTE-006 | Tenant-Scoped Route — Correct Tenant | Tenant-scoped routes accept requests with matching tenant context | Request tenant route with correct tenant, verify 200 |
| IT-ROUTE-007 | Tenant-Scoped Route — Wrong Tenant | Tenant-scoped routes reject requests with wrong tenant context | Request tenant route with wrong tenant, verify 403 |
| IT-ROUTE-008 | Tenant-Scoped Route — No Tenant | Tenant-scoped routes reject requests without tenant context | Request tenant route without tenant, verify 403 |
| IT-ROUTE-009 | Route Guard — Allow-List | Only explicitly allow-listed routes are public | Verify all other routes require auth |
| IT-ROUTE-010 | Route Guard — Method-Specific | Route guards apply per HTTP method (GET vs POST) | Verify method-specific access control |

#### Test Data Requirements

- Route allow-list configuration (public, authenticated, tenant-scoped)
- Valid/invalid authentication tokens
- Tenant context fixtures

---

### 3.7 F-MVKTMUSS-001D-92EB — Audit Events

**Objective:** Validate append-only audit logging, GDPR/PDPA compliance, and system actor recording.

#### Integration Test Cases

| Test ID | Test Name | Acceptance Criteria | Verification Method |
|---------|-----------|---------------------|---------------------|
| IT-AUDIT-001 | Append-Only — Insert | Audit events are inserted successfully | Verify event recorded in `audit_log` |
| IT-AUDIT-002 | Append-Only — No Update | Audit events cannot be updated | Attempt UPDATE, verify rejection |
| IT-AUDIT-003 | Append-Only — No Delete | Audit events cannot be deleted | Attempt DELETE, verify rejection |
| IT-AUDIT-004 | Chain Hash — Sequential | Each record's chain_hash incorporates previous record's hash | Verify chain integrity |
| IT-AUDIT-005 | Chain Hash — Tamper Detection | Modifying a record breaks chain verification | Modify record, verify chain verification fails |
| IT-AUDIT-006 | GDPR/PDPA — No Sensitive Data | Audit records do not contain NRIC, full bank account numbers | Verify redaction in audit payloads |
| IT-AUDIT-007 | GDPR/PDPA — Right to Erasure | Personal data can be anonymized on legal request | Verify anonymization process (compensating entry) |
| IT-AUDIT-008 | System Actor — Service Account | Service-initiated actions record `actor_type='service'` | Verify service actor recorded |
| IT-AUDIT-009 | System Actor — Cron Job | Cron-initiated actions record `actor_type='cron'` | Verify cron actor recorded |
| IT-AUDIT-010 | System Actor — External | External webhook callbacks record `actor_type='external'` | Verify external actor recorded |
| IT-AUDIT-011 | Meta-Audit — Query Logged | Queries against `audit_log` generate meta-audit records | Query audit log, verify meta-audit entry |
| IT-AUDIT-012 | Meta-Audit — Export Logged | Exports of `audit_log` generate meta-audit records | Export audit log, verify meta-audit entry |
| IT-AUDIT-013 | Tenant Isolation — Audit Log | Audit queries are tenant-scoped (RLS enforced) | Query audit log with tenant A context, verify zero tenant B rows |

#### Test Data Requirements

- Audit log schema with RLS enabled
- Sample audit events (restricted access, filing events, system events)
- Chain hash verification utility

#### Reference

See `docs/audit-log-design.md` for audit log schema and chain hash specification.
See `docs/audit-log-security-review.md` for security requirements and compliance standards.

---

### 3.8 F-MVKTMUTT-001F-JY4B — Abuse Protection

**Objective:** Validate rate limiting, generic errors, and no user enumeration.

#### Integration Test Cases

| Test ID | Test Name | Acceptance Criteria | Verification Method |
|---------|-----------|---------------------|---------------------|
| IT-ABUSE-001 | Rate Limit — Authentication Endpoint | Authentication endpoint enforces rate limit | Send N+1 requests, verify (N+1)th is rate-limited |
| IT-ABUSE-002 | Rate Limit — MFA Verification | MFA verification endpoint enforces rate limit | Send N+1 MFA attempts, verify (N+1)th is rate-limited |
| IT-ABUSE-003 | Rate Limit — Password Reset | Password reset endpoint enforces rate limit | Send N+1 reset requests, verify (N+1)th is rate-limited |
| IT-ABUSE-004 | Rate Limit — Response Headers | Rate limit headers returned (X-RateLimit-Limit, X-RateLimit-Remaining) | Verify response headers |
| IT-ABUSE-005 | Rate Limit — Retry-After | Rate-limited responses include Retry-After header | Verify Retry-After header on 429 |
| IT-ABUSE-006 | Generic Error — Invalid Credentials | Invalid credentials return generic error | Verify error message does not reveal "invalid password" |
| IT-ABUSE-007 | Generic Error — User Not Found | Non-existent user returns same error as invalid credentials | Verify error message identical for both cases |
| IT-ABUSE-008 | No User Enumeration — Timing | Response timing does not reveal user existence | Verify timing consistency for valid/invalid users |
| IT-ABUSE-009 | No User Enumeration — Error Code | Error codes are identical for user-not-found vs invalid-credentials | Verify HTTP status code consistency |
| IT-ABUSE-010 | Account Lockout — Threshold | Account is locked after N failed attempts | Verify account lockout after threshold |
| IT-ABUSE-011 | Account Lockout — Duration | Account remains locked for configured duration | Verify lockout expiration |
| IT-ABUSE-012 | Account Lockout — Notification | User notified of account lockout | Verify lockout notification |

#### Test Data Requirements

- Rate limit configuration (requests per minute, burst allowance)
- User fixtures for lockout testing
- Timing measurement utility

---

## 4. Test Execution Strategy

### 4.1 Test Environment

| Environment | Purpose | Data |
|-------------|---------|------|
| Local | Unit test development | Mock data, in-memory DB |
| CI (Staging) | Integration test execution | Seeded test data, isolated Postgres |
| Pre-Prod | Performance and security testing | Anonymized production-like data |

### 4.2 Test Execution Order

1. **Unit Tests** — Run on every commit, fast feedback (< 5 minutes)
2. **Integration Tests** — Run on PR, moderate feedback (< 15 minutes)
3. **Security Tests** — Run on PR, comprehensive coverage (< 30 minutes)
4. **Performance Tests** — Run on release candidate, full load simulation (< 60 minutes)

### 4.3 CI Gate Requirements

- All unit tests must pass (100% required)
- All integration tests must pass (100% required)
- Security tests must pass (no critical/high findings)
- Performance tests must meet SLO thresholds (p95 latency, error rate < 0.1%)

---

## 5. Acceptance Criteria Mapping to Slice Verification

| Slice Verification Criteria | Related Features | Test Cases |
|----------------------------|------------------|------------|
| User can sign in with MFA | F-MVKTMUKF-0010-L4YE, F-MVKTMUMQ-0013-YF80 | UT-ENTRA-*, UT-MFA-* |
| User can switch businesses | F-MVKTMUNQ-0015-S6VS | IT-MEMBER-*, UT-PERM-* |
| User accesses only their data | F-MVKTMUQ8-0019-1H2U | IT-RLS-* |
| Route coverage guard passes | F-MVKTMUR9-001B-2YS5 | IT-ROUTE-* |
| Revocation effective on next request | F-MVKTMUSS-001D-92EB | IT-AUDIT-*, IT-RLS-* |
| RLS test proves zero rows without context | F-MVKTMUQ8-0019-1H2U | IT-RLS-006, IT-RLS-007 |
| All auth events present in audit log | F-MVKTMUSS-001D-92EB | IT-AUDIT-* |

---

## 6. Out of Scope

- End-to-end UI testing (covered by separate E2E test suite)
- Load testing at production scale (covered by performance engineering team)
- Penetration testing (covered by security audit engagement)
- Disaster recovery testing (covered by SRE runbooks)

---

## 7. Dependencies and Prerequisites

| Dependency | Owner | Status |
|------------|-------|--------|
| PostgreSQL instance with RLS | Database Engineer | Required |
| Entra External ID tenant | SRE Engineer | Required |
| Mock email service | SRE Engineer | Required |
| Test data seeding scripts | QA Lead | In Progress |
| CI pipeline configuration | DevOps Engineer | Required |

---

## 8. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| RLS misconfiguration | High — cross-tenant data leakage | Automated RLS validation in CI, manual audit before release |
| Mock Entra keys not matching production | Medium — false positives in testing | Use production-like key rotation simulation |
| Rate limiting thresholds not tuned | Medium — DoS vulnerability or false positives | Performance testing with realistic load patterns |
| Audit log chain hash performance | Medium — write latency | Advisory lock optimization, partitioned chains |

---

## 9. Deliverables Checklist

- [x] Test plan document (this document)
- [ ] Test data strategy document (`docs/test-data/multi-tenant-kernel-auth.md`)
- [ ] Mocking strategy document (`docs/mocking-strategy/multi-tenant-kernel-auth.md`)
- [ ] Performance test hooks document (`docs/performance-test-hooks/multi-tenant-kernel-auth.md`)
- [ ] Security test checklist document (`docs/security-test-checklist/multi-tenant-kernel-auth.md`)
- [ ] Automated test suite implementation (follow-up task)
- [ ] CI pipeline integration (follow-up task)

---

## 10. Handoff Notes for QA Lead (agent-34863834)

**Priority:** This slice is the foundation of the platform and carries the highest security and compliance risk. Testing must be thorough and evidence-grade.

**Key Focus Areas:**
1. **RLS isolation** — This is the most critical security boundary. Zero tolerance for cross-tenant leakage.
2. **Audit log integrity** — Chain hash verification must be automated and run on every deployment.
3. **Generic error responses** — User enumeration is a common attack vector; verify consistency across all auth endpoints.
4. **Rate limiting** — Ensure rate limits are enforced at the edge (API gateway) and application layer.

**Recommended Next Steps:**
1. Review and approve this test plan
2. Implement test data fixtures (see `docs/test-data/multi-tenant-kernel-auth.md`)
3. Set up mocking infrastructure (see `docs/mocking-strategy/multi-tenant-kernel-auth.md`)
4. Implement unit tests for Entra and MFA validation
5. Implement integration tests for RLS and audit logging
6. Configure CI gates for automated test execution

**Open Questions:**
1. Confirm Entra External ID tenant availability for testing
2. Confirm rate limit thresholds (requests per minute) with security team
3. Confirm audit log retention period with legal counsel

---

*End of test strategy and plan document.*
