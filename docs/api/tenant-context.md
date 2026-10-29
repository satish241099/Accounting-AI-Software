# Tenant Context Propagation

## Overview

This document describes the X-Business-Id header propagation and database tenant context management for the multi-tenant kernel API.

## Route Classification Taxonomy

Route classification is the single source of truth for API security and authentication:

| Classification | Auth Required | Tenant Context | Routes |
|---------------|---------------|----------------|--------|
| **public** | No | No | `/health`, `/auth/callback` |
| **authenticated-no-tenant** | Yes (Bearer) | No | `/me`, `/me/businesses`, `/invites/accept`, `POST /businesses` |
| **tenant-scoped** | Yes (Bearer) | Yes (X-Business-Id) | All `/businesses/{id}` and other tenant operations |

## X-Business-Id Header

The `X-Business-Id` header identifies the tenant context for tenant-scoped routes.

### Requirements

- **Format**: UUID v4
- **Required**: For all tenant-scoped routes
- **Validation**: Must be a valid business where the authenticated user has membership
- **Propagation**: Value is propagated to `app.tenant_id` via `SET LOCAL` as the first statement of every transaction

### Example

```http
GET /businesses/12345678-1234-5678-9012-123456789012 HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
X-Business-Id: 12345678-1234-5678-9012-123456789012
```

## Database Tenant Context

### SET LOCAL app.tenant_id

The tenant context is set in the database using PostgreSQL's `SET LOCAL` command:

```sql
BEGIN;
SET LOCAL app.tenant_id = '12345678-1234-5678-9012-123456789012';
-- ... application queries ...
COMMIT;
```

### Key Properties

1. **First statement**: `SET LOCAL app.tenant_id` must be the first statement after `BEGIN`
2. **Transaction scoped**: Context is automatically reset on commit or rollback
3. **Bound parameter**: The tenant id is passed as a bound parameter, never string-interpolated
4. **Fail-closed**: If tenant context is not set, RLS policies deny access (no rows returned)

### RLS Policy Example

```sql
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON invoices
  USING      (tenant_id = current_setting('app.tenant_id', true)::uuid)
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
```

### Fail-Closed Behavior

When no tenant context is set or the context is invalid:

- **READ**: Returns zero rows (policy evaluates to NULL, which is not TRUE)
- **WRITE**: Rejected by `WITH CHECK` policy

This ensures that:
- No data leakage occurs through missing tenant context
- No data is written without proper tenant isolation
- Multi-tenant security is enforced at the database level

## Tenant Context Propagation Flow

```
Request → Auth → Business Validation → SET LOCAL → Queries → Commit
                    ↑
         X-Business-Id header validated against business_membership
```

### Step-by-Step:

1. **Request arrives** with `X-Business-Id` header
2. **Authentication validated** via Bearer token
3. **Business membership validated** for authenticated user
4. **Tenant context established**: `app.tenant_id` set to business UUID
5. **Transaction executes** with tenant isolation enforced
6. **Response returns** with tenant-scoped data only

## Implementation Notes

### For Application Developers

- Always begin tenant-scoped operations with `BEGIN`
- Always set `SET LOCAL app.tenant_id` as the first statement
- Never attempt to bypass tenant context
- Handle RLS denial errors gracefully

### For Test Engineers

- Test fail-closed behavior: request without X-Business-Id should return 403
- Test tenant isolation: user from business A cannot access business B's data
- Test response time: SET LOCAL is a single round trip through PgBouncer

### Database Requirements

- PostgreSQL 12+ with RLS
- PgBouncer in transaction pooling mode
- `app.tenant_id` setting enabled

## Error Cases

| Error Scenario | Response | Description |
|---------------|----------|-------------|
| Missing X-Business-Id | 401 | Header required for tenant-scoped routes |
| Invalid UUID format | 400 | Header must be valid UUID |
| User not in business | 403 | Tenant context validation failed |
| Business not found | 404 | Business does not exist |

## Security Considerations

- Tenant context is **never** user-settable directly
- Only validated business membership grants tenant access
- RLS policies are enforced at the database level
- Session variables are avoided to prevent cross-tenant leakage
- Pooler reset (`DISCARD ALL`) is mandatory for PgBouncer safety