# Multi-tenant Kernel & Auth — Test Data Strategy

**Task:** KB-018
**Slice:** SL-MVKTMUJW-000Y-KHRJ (Multi-tenant Kernel & Authentication)
**Created:** 2026-10-24
**Status:** Draft — Pending QA Lead Review

---

## 1. Executive Summary

This document defines the test data strategy for the Multi-tenant Kernel & Authentication slice. It specifies how tenant isolation fixtures, mock Entra signing keys, and MFA claim variants are generated, managed, and maintained to support the comprehensive test plan.

---

## 2. Design Principles

1. **Deterministic** — Test data fixtures produce consistent, reproducible results across environments.
2. **Isolated** — Test data for one feature does not interfere with test data for another feature.
3. **Self-Cleaning** — Test data is automatically cleaned up after each test execution.
4. **Production-Like** — Test data mirrors production data structures, volumes, and edge cases.
5. **No Secrets** — Test data never contains real secrets, tokens, or PII.

---

## 3. Tenant Isolation Fixtures

### 3.1 Fixture Architecture

Tenant isolation fixtures provide pre-configured tenant entities for testing cross-tenant data isolation.

```
test/fixtures/tenants/
├── tenant-a.json          # Tenant A primary fixture
├── tenant-b.json          # Tenant B primary fixture
├── tenant-c.json          # Tenant C for edge case testing
└── shared.json            # Shared reference data
```

### 3.2 Tenant A — Primary Test Tenant

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Test Tenant Alpha",
  "slug": "test-tenant-alpha",
  "status": "active",
  "created_at": "2026-01-01T00:00:00Z",
  "settings": {
    "mfa_required": true,
    "language": "en-MY"
  }
}
```

### 3.3 Tenant B — Isolation Test Tenant

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "name": "Test Tenant Beta",
  "slug": "test-tenant-beta",
  "status": "active",
  "created_at": "2026-01-01T00:00:00Z",
  "settings": {
    "mfa_required": false,
    "language": "en-MY"
  }
}
```

### 3.4 Tenant C — Edge Case Tenant

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "name": "Test Tenant Gamma",
  "slug": "test-tenant-gamma",
  "status": "suspended",
  "created_at": "2026-01-01T00:00:00Z",
  "settings": {
    "mfa_required": true,
    "language": "ms-MY"
  }
}
```

### 3.5 Seed Data per Tenant

Each tenant fixture includes seed data for the following entity types:

| Entity Type | Tenant A | Tenant B | Tenant C |
|-------------|----------|----------|----------|
| Users | 3 users | 3 users | 1 user |
| Roles | owner, admin, member | owner, admin | owner |
| Memberships | 3 memberships | 3 memberships | 1 membership |
| Clients | 2 clients | 2 clients | 0 clients |
| Invoices | 5 invoices | 5 invoices | 0 invoices |
| Payments | 3 payments | 3 payments | 0 payments |
| Audit Events | 10 events | 10 events | 1 event |

### 3.6 Fixture Generation

Fixtures are generated via a deterministic seed process:

```typescript
// test/fixtures/generate.ts
const SEED = 'multi-tenant-kernel-auth-test';

function generateTenantId(index: number): string {
  // Deterministic UUID from seed + index
  return sha256(`${SEED}-tenant-${index}`);
}

function generateUserId(tenantId: string, index: number): string {
  return sha256(`${tenantId}-user-${index}`);
}
```

### 3.7 Fixture Lifecycle Management

- **Setup:** Fixtures are loaded into the test database at the start of each test suite
- **Isolation:** Each test transaction resets fixtures to a known state
- **Teardown:** All test data is cleaned up after the test suite completes
- **Verification:** Fixture integrity is verified before each test run

---

## 4. Mock Entra Signing Keys

### 4.1 Key Pair Generation

Entra signing keys are mocked using self-generated RSA-256 and ECDSA key pairs for testing JWT validation:

```
test/fixtures/entra-keys/
├── rsa-256/
│   ├── private.pem      # RSA-256 private key (test only)
│   ├── public.pem       # RSA-256 public key (test only)
│   └── jwks.json        # JWKS endpoint response (RSA-256)
└── ec-256/
    ├── private.pem      # ECDSA P-256 private key (test only)
    ├── public.pem       # ECDSA P-256 public key (test only)
    └── jwks.json        # JWKS endpoint response (ECDSA)
```

### 4.2 RSA-256 JWKS Fixture

```json
{
  "keys": [
    {
      "kty": "RSA",
      "kid": "test-rsa-key-001",
      "use": "sig",
      "alg": "RS256",
      "n": "(base64url-encoded modulus)",
      "e": "AQAB"
    }
  ]
}
```

### 4.3 ECDSA P-256 JWKS Fixture

```json
{
  "keys": [
    {
      "kty": "EC",
      "kid": "test-ec-key-001",
      "use": "sig",
      "alg": "ES256",
      "crv": "P-256",
      "x": "(base64url-encoded x coordinate)",
      "y": "(base64url-encoded y coordinate)"
    }
  ]
}
```

### 4.4 Key Rotation Simulation

Key rotation is simulated by:
1. Generating multiple key pairs with different `kid` values
2. Configuring the mock JWKS endpoint to return specific keys
3. Testing scenarios:
   - Token signed with active key → accepted
   - Token signed with rotated (expired) key → rejected
   - Token signed with future key (not yet in JWKS) → rejected
   - JWKS returns multiple keys → correct key selected by `kid`

### 4.5 Token Generation Utility

```typescript
// test/fixtures/token-generator.ts
import jwt from 'jsonwebtoken';

function generateEntraToken(payload: Partial<EntraClaims>, options: TokenOptions = {}): string {
  const defaults = {
    iss: 'https://accounts.accesscontrol.windows.net/test-tenant/',
    aud: 'test-client-id',
    exp: Math.floor(Date.now() / 1000) + 3600,
    nbf: Math.floor(Date.now() / 1000) - 60,
    iat: Math.floor(Date.now() / 1000) - 60,
    ...payload,
  };

  return jwt.sign(defaults, privateKey, {
    algorithm: options.algorithm || 'RS256',
    keyid: options.kid || 'test-rsa-key-001',
  });
}
```

---

## 5. MFA Claim Variants

### 5.1 MFA Claim Structure

MFA claims follow Microsoft Entra External ID conventions:

```json
{
  "amr": ["pwd", "mfa"],           // Authentication Methods Reference
  "xms_mfa": "pass",               // MFA status
  "xms_mfa_challenge": "totp",     // MFA challenge type
  "auth_time": "2026-10-24T10:00:00Z" // Authentication timestamp
}
```

### 5.2 MFA Claim Variants

| Variant | Description | `amr` | `xms_mfa` | Use Case |
|---------|-------------|-------|-----------|----------|
| Valid MFA | Successful MFA verification | `["pwd", "mfa"]` | `"pass"` | Happy path |
| Missing MFA | No MFA performed | `["pwd"]` | `undefined` | MFA required scenario |
| Failed MFA | MFA verification failed | `["pwd"]` | `"fail"` | MFA failure scenario |
| Expired MFA | MFA token expired | `["pwd", "mfa"]` | `"pass"` (old `auth_time`) | MFA expiry scenario |
| Tampered MFA | MFA claim modified | `["pwd", "mfa"]` | `"pass"` (signed with different key) | Security test |

### 5.3 MFA Claim Fixtures

```typescript
// test/fixtures/mfa-claims.ts

export const VALID_MFA_CLAIMS = {
  amr: ['pwd', 'mfa'],
  xms_mfa: 'pass',
  xms_mfa_challenge: 'totp',
  auth_time: new Date().toISOString(),
};

export const MISSING_MFA_CLAIMS = {
  amr: ['pwd'],
  // xms_mfa absent
};

export const FAILED_MFA_CLAIMS = {
  amr: ['pwd'],
  xms_mfa: 'fail',
};

export const EXPIRED_MFA_CLAIMS = {
  amr: ['pwd', 'mfa'],
  xms_mfa: 'pass',
  xms_mfa_challenge: 'totp',
  auth_time: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
};
```

### 5.4 Risk Level Configurations

| Risk Level | MFA Required | Test Scenario |
|-----------|--------------|---------------|
| High | Always | Account settings change, password reset, new device login |
| Medium | Conditional | First login of the day, new IP address |
| Low | Optional | Data access operations |

---

## 6. User and Role Fixtures

### 6.1 User Fixtures

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440100",
  "email": "owner@test-tenant-alpha.com",
  "display_name": "Test Owner",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440001",
  "role": "owner",
  "status": "active",
  "mfa_enabled": true,
  "created_at": "2026-01-01T00:00:00Z",
  "last_login": "2026-10-24T10:00:00Z"
}
```

### 6.2 Role Definitions

| Role ID | Name | Permissions |
|---------|------|-------------|
| `owner` | Owner | All permissions, ownership transfer, member management |
| `admin` | Administrator | Administrative operations, member management, no ownership transfer |
| `member` | Standard Member | Operational tasks (invoicing, payments, reporting) |
| `external_accountant` | External Accountant | Read-only financial data access, no sensitive data |

### 6.3 Permission Matrix Fixture

```json
{
  "owner": {
    "read_all": true,
    "write_all": true,
    "delete_all": true,
    "manage_members": true,
    "transfer_ownership": true,
    "view_audit_log": true,
    "access_sensitive_data": true,
    "manage_settings": true
  },
  "admin": {
    "read_all": true,
    "write_all": true,
    "delete_all": false,
    "manage_members": true,
    "transfer_ownership": false,
    "view_audit_log": true,
    "access_sensitive_data": true,
    "manage_settings": true
  },
  "member": {
    "read_all": false,
    "write_all": false,
    "delete_all": false,
    "manage_members": false,
    "transfer_ownership": false,
    "view_audit_log": false,
    "access_sensitive_data": false,
    "manage_settings": false
  },
  "external_accountant": {
    "read_all": false,
    "write_all": false,
    "delete_all": false,
    "manage_members": false,
    "transfer_ownership": false,
    "view_audit_log": false,
    "access_sensitive_data": false,
    "manage_settings": false
  }
}
```

---

## 7. Invitation Token Fixtures

### 7.1 Token Lifecycle States

| State | Description | Test Use |
|-------|-------------|----------|
| `valid` | Active invitation, within expiration window | Acceptance test |
| `expired` | Invitation past expiration window | Rejection test |
| `consumed` | Invitation already accepted | Re-use rejection test |
| `revoked` | Invitation manually cancelled | Cancellation test |

### 7.2 Invitation Fixture Structure

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440200",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440001",
  "invitee_email": "new-member@test-tenant-alpha.com",
  "inviter_id": "550e8400-e29b-41d4-a716-446655440100",
  "role": "member",
  "token": "test-invitation-token-001",
  "state": "valid",
  "expires_at": "2027-10-24T10:00:00Z",
  "created_at": "2026-10-24T10:00:00Z"
}
```

---

## 8. Audit Event Fixtures

### 8.1 Sample Audit Events

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440300",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440001",
  "occurred_at": "2026-10-24T10:00:00Z",
  "actor_id": "550e8400-e29b-41d4-a716-446655440100",
  "actor_type": "user",
  "action": "restricted.read",
  "entity_type": "bank_credential",
  "entity_id": "550e8400-e29b-41d4-a716-446655440400",
  "entity_tenant_id": "550e8400-e29b-41d4-a716-446655440001",
  "request_id": "550e8400-e29b-41d4-a716-446655440500",
  "outcome": "success",
  "metadata": {
    "ip_address": "127.0.0.1",
    "user_agent": "TestAgent/1.0"
  },
  "before_state": null,
  "after_state": null,
  "chain_hash": "deadbeef...",
  "created_at": "2026-10-24T10:00:00Z"
}
```

### 8.2 Audit Event Categories

| Category | Actions | Fixture Count |
|----------|---------|---------------|
| Restricted access | `restricted.read`, `restricted.write` | 5 each |
| Filing events | `filing.submit`, `filing.validate` | 5 each |
| Audit access | `audit.query`, `audit.export` | 3 each |
| System events | `system.migration`, `system.config_change` | 3 each |
| Tenant lifecycle | `tenant.create`, `tenant.delete` | 2 each |

---

## 9. Rate Limiting Test Data

### 9.1 Rate Limit Configuration Fixtures

```json
{
  "authentication": {
    "max_requests_per_minute": 5,
    "burst_allowance": 10,
    "lockout_threshold": 5,
    "lockout_duration_ms": 900000
  },
  "mfa_verification": {
    "max_requests_per_minute": 10,
    "burst_allowance": 20,
    "lockout_threshold": 10,
    "lockout_duration_ms": 600000
  },
  "password_reset": {
    "max_requests_per_minute": 3,
    "burst_allowance": 5,
    "lockout_threshold": 3,
    "lockout_duration_ms": 1800000
  }
}
```

### 9.2 Timing Measurement

Timing measurements use a deterministic clock mock:

```typescript
// test/utils/clock-mock.ts
class MockClock {
  private _time: number;

  constructor(startTime: number) {
    this._time = startTime;
  }

  getTime(): number {
    return this._time;
  }

  advance(ms: number): void {
    this._time += ms;
  }
}
```

---

## 10. Data Generation and Maintenance

### 10.1 Fixture Generation Script

A single script generates all test fixtures:

```bash
pnpm run test:generate-fixtures
```

This script:
1. Generates tenant fixtures with deterministic UUIDs
2. Generates user fixtures for each tenant
3. Generates role and permission fixtures
4. Generates mock Entra signing keys
5. Generates MFA claim variants
6. Generates invitation token fixtures
7. Generates audit event fixtures

### 10.2 Fixture Validation

Before each test run, fixtures are validated:

```bash
pnpm run test:validate-fixtures
```

Validation checks:
1. UUID format and uniqueness
2. Referential integrity between fixtures
3. Required fields present
4. No production-like data (secrets, real PII)

### 10.3 Fixture Versioning

Fixtures are versioned alongside code changes:

```
test/fixtures/
├── v1/
│   ├── tenants/
│   ├── users/
│   └── ...
├── v2/
│   ├── tenants/
│   └── ...
└── CURRENT -> v2
```

---

## 11. Environment-Specific Considerations

### 11.1 Local Development

- Fixtures loaded from `test/fixtures/` directory
- In-memory database for unit tests
- Mock Entra JWKS endpoint on localhost

### 11.2 CI Environment

- Fixtures loaded from versioned fixture sets
- Isolated PostgreSQL instance with RLS enabled
- Mock services started as containers

### 11.3 Pre-Production

- Anonymized production-like data generated from schema
- Real Entra tenant (test) connected
- Real email service (test domain) connected

---

*End of test data strategy document.*
