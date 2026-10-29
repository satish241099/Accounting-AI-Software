# Shared Error Schema

## Overview

This document defines the shared error schema for the multi-tenant kernel API, including the ACXO-058-style refusal_reason enum.

## Common Error Schema

All API responses that contain an error use the following schema:

```typescript
interface Error {
  code: string;              // Machine-readable error code
  message: string;             // Human-readable error message
  refusal_reason?: RefusalReason; // ACXO-058-style refusal reason (optional)
  details?: Record<string, any>;  // Additional error details
  trace_id?: string;           // Request trace identifier for support
}
```

## RefusalReason Enum

The `RefusalReason` enum provides standardized reasons why a request was refused:

```typescript
enum RefusalReason {
  no_evidence = 'no_evidence',        // Insufficient evidence to fulfill request
  blocked_source = 'blocked_source',  // Requested source is blocked
  restricted_content = 'restricted_content', // Requested content is restricted
  schema_violation = 'schema_violation',     // Request violates schema constraints
  citation_missing = 'citation_missing'      // Required citation is missing
}
```

### RefusalReason Values

| Value | Description | Use Case |
|-------|-------------|----------|
| `no_evidence` | Insufficient evidence to fulfill request | Request lacks required data or context |
| `blocked_source` | Requested source is blocked | Attempting to access blocked URL/domain |
| `restricted_content` | Requested content is restricted | Accessing content the user cannot see |
| `schema_violation` | Request violates schema constraints | Request body doesn't match expected schema |
| `citation_missing` | Required citation is missing | Required attribution or source not provided |

## Error Codes

### Authentication Errors

| Code | HTTP Status | RefusalReason | Message |
|------|-------------|---------------|---------|
| `AUTH_REQUIRED` | 401 | - | Authentication required |
| `AUTH_INVALID` | 401 | - | Invalid authentication credentials |
| `AUTH_EXPIRED` | 401 | - | Authentication token expired |

### Authorization Errors

| Code | HTTP Status | RefusalReason | Message |
|------|-------------|---------------|---------|
| `ACCESS_DENIED` | 403 | restricted_content | Access denied to resource |
| `TENANT_FORBIDDEN` | 403 | restricted_content | Not a member of the specified business |

### Validation Errors

| Code | HTTP Status | RefusalReason | Message |
|------|-------------|---------------|---------|
| `VALIDATION_ERROR` | 400 | schema_violation | Request validation failed |
| `REQUIRED_FIELD` | 400 | schema_violation | Required field missing |
| `INVALID_FORMAT` | 400 | schema_violation | Invalid format for field |

### Not Found Errors

| Code | HTTP Status | RefusalReason | Message |
|------|-------------|---------------|---------|
| `NOT_FOUND` | 404 | - | Resource not found |
| `BUSINESS_NOT_FOUND` | 404 | - | Business not found |

### Tenant Context Errors

| Code | HTTP Status | RefusalReason | Message |
|------|-------------|---------------|---------|
| `TENANT_CONTEXT_MISSING` | 403 | - | X-Business-Id header required |
| `TENANT_CONTEXT_INVALID` | 403 | restricted_content | Invalid tenant context |

### System Errors

| Code | HTTP Status | RefusalReason | Message |
|------|-------------|---------------|---------|
| `INTERNAL_ERROR` | 500 | - | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | - | Service temporarily unavailable |

## Usage Examples

### Validation Error with RefusalReason

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Request body validation failed",
  "refusal_reason": "schema_violation",
  "details": {
    "field": "email",
    "reason": "Invalid email format"
  },
  "trace_id": "12345678-1234-5678-9012-123456789012"
}
```

### Access Denied with RefusalReason

```json
{
  "code": "ACCESS_DENIED",
  "message": "User is not authorized to access this resource",
  "refusal_reason": "restricted_content",
  "trace_id": "12345678-1234-5678-9012-123456789012"
}
```

### Tenant Context Error

```json
{
  "code": "TENANT_FORBIDDEN",
  "message": "User is not a member of the specified business",
  "details": {
    "business_id": "12345678-1234-5678-9012-123456789012"
  },
  "trace_id": "12345678-1234-5678-9012-123456789012"
}
```

## OpenAPI Schema Definition

The error schema is defined in `docs/api/kernel-openapi.yaml` under `components.schemas.Error`:

```yaml
Error:
  type: object
  required:
    - code
    - message
  properties:
    code:
      type: string
      description: Machine-readable error code
    message:
      type: string
      description: Human-readable error message
    refusal_reason:
      $ref: '#/components/schemas/RefusalReason'
    details:
      type: object
      additionalProperties: true
    trace_id:
      type: string
      format: uuid
      description: Request trace identifier for support
```

## Design Principles

1. **Consistency**: All errors follow the same structure
2. **Traceability**: Every error includes a trace_id for debugging
3. **Machine-readable**: Error codes allow programmatic handling
4. **Human-readable**: Messages explain the error in plain language
5. **Standardized reasons**: RefusalReason enum enables consistent categorization

## Audit Logging

All access denials and validation failures should be logged with:
- The refusal_reason when available
- The attempted tenant context
- The requesting user/service
- The resource attempted to be accessed