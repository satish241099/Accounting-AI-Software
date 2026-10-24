# Multi-tenant Kernel & Auth — Mocking Strategy

**Task:** KB-018
**Slice:** SL-MVKTMUJW-000Y-KHRJ (Multi-tenant Kernel & Authentication)
**Created:** 2026-10-24
**Status:** Draft — Pending QA Lead Review

---

## 1. Executive Summary

This document defines the mocking and stubbing strategy for external dependencies in the Multi-tenant Kernel & Authentication slice. It specifies how Entra ID, MyInvois, and email services are mocked to enable isolated, deterministic testing.

---

## 2. Mocking Principles

1. **Isolation** — Tests do not depend on external services being available
2. **Determinism** — Mock responses are consistent and reproducible
3. **Realism** — Mock behaviors accurately simulate real service responses
4. **Performance** — Mock tests run faster than integration tests with real services
5. **Observability** — Mock interactions are logged for test verification

---

## 3. Entra External ID Mocking Strategy

### 3.1 Service Interface

Entra External ID provides authentication tokens via OpenID Connect protocol:

```typescript
interface EntraExternalID {
  getSigningKeys(): Promise<JWK[]>;
  validateToken(token: string): Promise<ValidatedToken>;
  introspectToken(token: string): Promise<TokenIntrospection>;
}
```

### 3.2 Mock Implementation

```typescript
// test/mocks/entra-external-id.mock.ts

export class MockEntraExternalID implements EntraExternalID {
  private signingKeys: JWK[];
  private validTokens: Map<string, ValidatedToken>;

  constructor() {
    this.signingKeys = loadFixtures('entra-keys/rsa-256/jwks.json');
    this.validTokens = new Map();
  }

  async getSigningKeys(): Promise<JWK[]> {
    return this.signingKeys;
  }

  async validateToken(token: string): Promise<ValidatedToken> {
    // Return pre-configured response or throw based on test scenario
    if (this.validTokens.has(token)) {
      return this.validTokens.get(token)!;
    }

    // Decode token to determine validation outcome
    const decoded = decodeToken(token);
    if (!decoded) {
      throw new Error('Invalid token format');
    }

    // Check expiration
    if (decoded.exp < Math.floor(Date.now() / 1000)) {
      throw new Error('Token expired');
    }

    // Check signature (mock verification)
    if (!this.verifySignature(token)) {
      throw new Error('Invalid signature');
    }

    return this.generateValidResponse(decoded);
  }
}
```

### 3.3 Mock Scenarios

| Scenario | Mock Behavior | Test Use |
|----------|---------------|----------|
| Valid token | Returns valid claims with MFA | Success path |
| Expired token | Throws "Token expired" error | Token expiry handling |
| Invalid signature | Throws "Invalid signature" error | Signature validation |
| Wrong issuer | Returns claims with wrong `iss` | Issuer validation |
| Wrong audience | Returns claims with wrong `aud` | Audience validation |
| JWKS fetch failure | Throws network error | Error handling |
| Key rotation | Returns new keys | Key rotation handling |

### 3.4 Mock JWKS Endpoint

A mock HTTP server simulates Entra's JWKS endpoint:

```bash
# Start mock JWKS server
pnpm run mock:entra-jwks
```

Response:

```json
GET /.well-known/jwks.json
{
  "keys": [
    {
      "kty": "RSA",
      "kid": "test-rsa-key-001",
      "use": "sig",
      "alg": "RS256",
      "n": "...",
      "e": "AQAB"
    }
  ]
}
```

### 3.5 Configuration

Tests configure Entra mocking via environment variables:

```env
ENTRA_MOCK_ENABLED=true
ENTRA_JWKS_URL=http://localhost:8080/.well-known/jwks.json
ENTRA_CLIENT_ID=test-client-id
ENTRA_TENANT_ID=test-tenant-id
```

---

## 4. MyInvois Service Mocking Strategy

### 4.1 Service Interface

MyInvois is Malaysia's e-invoicing service (LHDN):

```typescript
interface MyInvois {
  submitInvoice(invoice: Invoice): Promise<SubmissionResult>;
  getInvoiceStatus(referenceId: string): Promise<InvoiceStatus>;
  getValidationResults(referenceId: string): Promise<ValidationResult>;
}
```

### 4.2 Mock Implementation

```typescript
// test/mocks/myinvois.mock.ts

export class MockMyInvois implements MyInvois {
  private submissions: Map<string, SubmissionResult>;
  private statusUpdates: Map<string, InvoiceStatus>;

  async submitInvoice(invoice: Invoice): Promise<SubmissionResult> {
    // Simulate network latency
    await delay(100);

    // Validate invoice format (mock validation)
    if (!invoice.documentNumber) {
      return {
        status: 'rejected',
        reason: 'missing_document_number',
      };
    }

    // Generate reference ID
    const referenceId = generateReferenceId();

    // Store submission
    this.submissions.set(referenceId, {
      status: 'accepted',
      referenceId,
      submittedAt: new Date(),
    });

    return {
      status: 'accepted',
      referenceId,
    };
  }

  async getInvoiceStatus(referenceId: string): Promise<InvoiceStatus> {
    const submission = this.submissions.get(referenceId);
    if (!submission) {
      throw new Error('Submission not found');
    }

    // Simulate async processing
    return {
      ...submission,
      status: simulateStatusProgression(submission),
    };
  }
}
```

### 4.3 Mock Scenarios

| Scenario | Mock Behavior | Test Use |
|----------|---------------|----------|
| Valid invoice | Accepted, reference ID returned | Success path |
| Invalid invoice | Rejected with validation error | Validation handling |
| Network timeout | Throws timeout error | Retry logic |
| Service unavailable | Returns 503 error | Fallback handling |
| Status polling | Returns progressive status updates | Async processing |

### 4.4 Mock Service Configuration

```env
MYINVOIS_MOCK_ENABLED=true
MYINVOIS_BASE_URL=http://localhost:8081
MYINVOIS_MOCK_LATENCY_MS=100
MYINVOIS_MOCK_ERROR_RATE=0.01
```

---

## 5. Email Service Mocking Strategy

### 5.1 Service Interface

Email service for sending invitation emails and notifications:

```typescript
interface EmailService {
  sendEmail(params: EmailParams): Promise<EmailResult>;
  getSentEmails(): EmailRecord[];
  clearSentEmails(): void;
}
```

### 5.2 Mock Implementation

```typescript
// test/mocks/email-service.mock.ts

export class MockEmailService implements EmailService {
  private sentEmails: EmailRecord[] = [];

  async sendEmail(params: EmailParams): Promise<EmailResult> {
    // Validate parameters
    if (!params.to || !params.subject || !params.html) {
      throw new Error('Invalid email parameters');
    }

    // Simulate sending
    const emailRecord: EmailRecord = {
      id: generateId(),
      ...params,
      sentAt: new Date(),
      status: 'sent',
    };

    this.sentEmails.push(emailRecord);

    return {
      success: true,
      messageId: emailRecord.id,
    };
  }

  getSentEmails(): EmailRecord[] {
    return [...this.sentEmails];
  }

  clearSentEmails(): void {
    this.sentEmails = [];
  }
}
```

### 5.3 Mock Scenarios

| Scenario | Mock Behavior | Test Use |
|----------|---------------|----------|
| Valid email | Email sent, record stored | Success path |
| Invalid recipient | Throws "Invalid recipient" error | Validation |
| Template rendering | Renders template with context | Personalization |
| High volume | Batches emails efficiently | Performance |
| Service failure | Throws network error | Error handling |

### 5.4 Test Verification

Tests verify email content without depending on real email delivery:

```typescript
// Example test
test('sends invitation email on user invite', async () => {
  await userService.inviteUser(email, tenantId);
  
  const sentEmails = emailService.getSentEmails();
  expect(sentEmails).toHaveLength(1);
  expect(sentEmails[0].to).toBe(email);
  expect(sentEmails[0].subject).toContain('Invitation');
  expect(sentEmails[0].html).toContain(invitationToken);
});
```

---

## 6. Database Mocking Strategy

### 6.1 PostgreSQL Testing Approaches

**Unit Tests:** Use in-memory SQLite with SQL translation layer
**Integration Tests:** Use real PostgreSQL with test database and RLS
**Hybrid:** Use `testcontainers` to spin up disposable PostgreSQL

### 6.2 Test Database Setup

```bash
# Create test database
createdb test_multi_tenant_kernel_auth

# Run migrations
pnpm run db:migrate:test

# Load fixtures
pnpm run db:seed:test
```

### 6.3 Database Mocking for Unit Tests

```typescript
// test/mocks/database.mock.ts

export class MockDatabase {
  private data: Map<string, any[]> = new Map();

  async query(sql: string, params?: any[]): Promise<QueryResult> {
    // Parse SQL and return mock data
    const tableName = extractTableName(sql);
    const data = this.data.get(tableName) || [];
    
    // Apply WHERE clauses
    const filteredData = applyFilters(data, sql, params);
    
    return {
      rows: filteredData,
      rowCount: filteredData.length,
    };
  }
}
```

**Recommendation:** Prefer real PostgreSQL over mocks for database tests. RLS behavior is complex and difficult to mock correctly.

---

## 7. HTTP Client Mocking

### 7.1 MSW (Mock Service Worker)

MSW intercepts HTTP requests at the network level:

```typescript
// test/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('https://login.microsoftonline.com/*/discovery/v2.0/keys', () => {
    return HttpResponse.json({
      keys: loadFixtures('entra-keys/jwks.json'),
    });
  }),
  
  http.post('https://api.myinvois.gov.my/submit', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      referenceId: generateReferenceId(),
      status: 'accepted',
    });
  }),
];
```

### 7.2 Usage in Tests

```typescript
// test/setup.ts
import { setupServer } from 'msw/node';
import { handlers } from './mocks/handlers';

const server = setupServer(...handlers);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

---

## 8. Mock Coordination

### 8.1 Mock Server Orchestration

Start all mock services together:

```bash
pnpm run mock:start
```

This starts:
- Entra JWKS server (port 8080)
- MyInvois mock server (port 8081)
- Email service mock (in-process)

### 8.2 Mock State Management

Mock state is reset between tests:

```typescript
afterEach(() => {
  entraMock.reset();
  myinvoisMock.reset();
  emailMock.clearSentEmails();
  databaseMock.reset();
});
```

### 8.3 Mock Configuration per Test

Tests can configure mock behavior per scenario:

```typescript
test('handles Entra key rotation', async () => {
  entraMock.setKeys(['key-v1', 'key-v2']);
  
  // Test with old key
  const token1 = generateTokenWithKey('key-v1');
  
  // Mock rotates keys
  entraMock.rotateKeys(['key-v2']);
  
  // Test with new key
  const token2 = generateTokenWithKey('key-v2');
});
```

---

## 9. Mock Verification

### 9.1 Interaction Logging

All mock interactions are logged:

```typescript
// test/mocks/logger.ts
export class MockLogger {
  logs: MockInteraction[] = [];

  logInteraction(service: string, method: string, params: any, result: any): void {
    this.logs.push({
      service,
      method,
      params,
      result,
      timestamp: new Date(),
    });
  }
}
```

### 9.2 Verification Assertions

Tests verify mock interactions:

```typescript
test('calls Entra validateToken', async () => {
  await authService.validateToken(token);
  
  expect(entraMock.logs).toContainEqual({
    service: 'EntraExternalID',
    method: 'validateToken',
    params: [token],
  });
});
```

---

## 10. Best Practices

### 10.1 Do's

- ✅ Use mocks to isolate external dependencies
- ✅ Configure mock behavior via test fixtures
- ✅ Verify mock interactions in assertions
- ✅ Reset mock state between tests
- ✅ Log mock interactions for debugging

### 10.2 Don'ts

- ❌ Don't mock internal business logic
- ❌ Don't use real external services in unit tests
- ❌ Don't share mock state between tests
- ❌ Don't mock what you don't understand
- ❌ Don't use production data in mocks

---

## 11. Testing Mock Accuracy

### 11.1 Contract Tests

Contract tests verify mocks match real service behavior:

```typescript
test('mock Entra matches real Entra response format', async () => {
  const mockResponse = await mockEntra.getSigningKeys();
  const realResponse = await realEntra.getSigningKeys();
  
  expect(mockResponse).toMatchSchema(realResponse.schema);
});
```

### 11.2 Integration Validation

Periodically run tests against real services in staging:

```bash
pnpm run test:integration:real-services
```

---

*End of mocking strategy document.*
