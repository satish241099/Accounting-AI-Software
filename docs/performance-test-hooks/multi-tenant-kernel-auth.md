# Multi-tenant Kernel & Auth — Performance Test Hooks

**Task:** KB-018
**Slice:** SL-MVKTMUJW-000Y-KHRJ (Multi-tenant Kernel & Authentication)
**Created:** 2026-10-24
**Status:** Draft — Pending QA Lead Review

---

## 1. Executive Summary

This document defines performance test hooks for the auth hot path (token validation latency, concurrent session limits) in the Multi-tenant Kernel & Authentication slice. It specifies how to instrument, measure, and validate performance characteristics.

---

## 2. Auth Hot Path Definition

The auth hot path represents the critical path for authentication operations:

```
Client Request → API Gateway → Auth Middleware → Token Validation → Entra JWKS Fetch → Signature Verification → MFA Check → Tenant Context Set → Database Query → Audit Log Write → Response
```

### 2.1 Critical Operations

| Operation | Description | Target Latency |
|-----------|-------------|----------------|
| Token Validation | Validate JWT signature and claims | < 50ms p95 |
| MFA Validation | Check MFA claim and conditional requirements | < 30ms p95 |
| Tenant Context Switch | Set `app.tenant_id` for new request | < 10ms p95 |
| RLS Query | Execute tenant-scoped database query | < 100ms p95 |
| Audit Log Write | Write authentication event to audit log | < 20ms p95 (async) |
| Session Acquisition | Acquire/new session from auth service | < 50ms p95 |

---

## 3. Performance Test Hooks

### 3.1 Token Validation Latency Hook

```typescript
// src/auth/hooks/performance/token-validation.ts

export async function validateTokenWithMetrics(token: string): Promise<ValidatedToken> {
  const startTime = performance.now();
  const startMemory = process.memoryUsage();

  try {
    const result = await validateToken(token);
    
    const endTime = performance.now();
    const endMemory = process.memoryUsage();

    metrics.histogram('auth.token_validation.duration_ms', {
      value: endTime - startTime,
      tags: {
        valid: 'true',
        algorithm: result.algorithm,
      },
    });

    metrics.histogram('auth.token_validation.memory_bytes', {
      value: endMemory.heapUsed - startMemory.heapUsed,
      tags: {
        valid: 'true',
      },
    });

    return result;
  } catch (error) {
    const endTime = performance.now();
    
    metrics.histogram('auth.token_validation.duration_ms', {
      value: endTime - startTime,
      tags: {
        valid: 'false',
        error_type: error.name,
      },
    });

    throw error;
  }
}
```

### 3.2 MFA Validation Latency Hook

```typescript
// src/auth/hooks/performance/mfa-validation.ts

export async function validateMFAWithMetrics(claims: AuthClaims): Promise<MFAValidationResult> {
  const startTime = performance.now();

  try {
    const result = await validateMFA(claims);
    
    metrics.histogram('auth.mfa_validation.duration_ms', {
      value: performance.now() - startTime,
      tags: {
        required: String(result.required),
        valid: String(result.valid),
      },
    });

    return result;
  } catch (error) {
    metrics.histogram('auth.mfa_validation.duration_ms', {
      value: performance.now() - startTime,
      tags: {
        error: error.name,
      },
    });

    throw error;
  }
}
```

### 3.3 Tenant Context Switch Hook

```typescript
// src/db/hooks/performance/tenant-context.ts

export async function setTenantContextWithMetrics(tenantId: string): Promise<void> {
  const startTime = performance.now();

  try {
    await db.query('SET LOCAL app.tenant_id = $1', [tenantId]);
    
    metrics.histogram('db.tenant_context.duration_ms', {
      value: performance.now() - startTime,
      tags: {
        success: 'true',
      },
    });
  } catch (error) {
    metrics.histogram('db.tenant_context.duration_ms', {
      value: performance.now() - startTime,
      tags: {
        success: 'false',
      },
    });

    throw error;
  }
}
```

### 3.4 RLS Query Performance Hook

```typescript
// src/db/hooks/performance/rls-query.ts

export async function executeRLSQueryWithMetrics<T>(
  query: string,
  params: any[]
): Promise<T[]> {
  const startTime = performance.now();

  try {
    const result = await db.query(query, params);
    
    metrics.histogram('db.rls_query.duration_ms', {
      value: performance.now() - startTime,
      tags: {
        rows_returned: String(result.rows.length),
        query_type: extractQueryType(query),
      },
    });

    metrics.histogram('db.rls_query.rows_returned', {
      value: result.rows.length,
    });

    return result.rows;
  } catch (error) {
    metrics.histogram('db.rls_query.duration_ms', {
      value: performance.now() - startTime,
      tags: {
        error: error.name,
      },
    });

    throw error;
  }
}
```

### 3.5 Audit Log Write Hook

```typescript
// src/audit/hooks/performance/audit-write.ts

export async function writeAuditEventWithMetrics(event: AuditEvent): Promise<void> {
  const startTime = performance.now();
  let success = false;

  try {
    await auditLog.write(event);
    success = true;
  } finally {
    metrics.histogram('audit.write.duration_ms', {
      value: performance.now() - startTime,
      tags: {
        success: String(success),
        action: event.action,
        entity_type: event.entityType,
      },
    });

    metrics.counter('audit.write.count', 1, {
      action: event.action,
      success: String(success),
    });
  }
}
```

---

## 4. Concurrent Session Limits

### 4.1 Session Limit Hook

```typescript
// src/auth/hooks/performance/session-limits.ts

export class SessionLimitManager {
  private activeSessions = new Map<string, number>();
  private maxConcurrentSessionsPerUser = 5;
  private maxConcurrentSessionsPerTenant = 1000;

  async checkSessionLimit(userId: string, tenantId: string): Promise<void> {
    const startTime = performance.now();

    const userSessions = this.activeSessions.get(userId) || 0;
    const tenantSessions = this.getTenantSessionCount(tenantId);

    if (userSessions >= this.maxConcurrentSessionsPerUser) {
      metrics.counter('auth.session_limit.exceeded', 1, {
        limit_type: 'user',
      });

      throw new Error('Maximum concurrent sessions exceeded');
    }

    if (tenantSessions >= this.maxConcurrentSessionsPerTenant) {
      metrics.counter('auth.session_limit.exceeded', 1, {
        limit_type: 'tenant',
      });

      throw new Error('Tenant session limit exceeded');
    }

    metrics.histogram('auth.session_limit.check.duration_ms', {
      value: performance.now() - startTime,
      tags: {
        user_sessions: String(userSessions),
        tenant_sessions: String(tenantSessions),
      },
    });
  }
}
```

### 4.2 Session Count Metrics

```typescript
// Session count gauges updated periodically
setInterval(() => {
  metrics.gauge('auth.sessions.active.total', activeSessionCount);
  metrics.gauge('auth.sessions.active.per_tenant', 
    getTenantSessionCounts()
  );
  metrics.gauge('auth.sessions.active.per_user',
    getUserSessionCounts()
  );
}, 60000); // Update every minute
```

---

## 5. End-to-End Auth Flow Performance Hook

```typescript
// src/auth/hooks/performance/e2e-auth-flow.ts

export async function measureAuthFlow(request: AuthRequest): Promise<AuthResponse> {
  const startTime = performance.now();
  const traceId = generateTraceId();

  metrics.timer('auth.e2e.duration_ms', (timer) => {
    logger.info('Auth flow started', { traceId, userId: request.userId });

    return validateToken(request.token)
      .then(() => {
        metrics.step('token_validation');
        return validateMFA(request.claims);
      })
      .then(() => {
        metrics.step('mfa_validation');
        return setTenantContext(request.tenantId);
      })
      .then(() => {
        metrics.step('tenant_context');
        return executeRLSQuery(request.query);
      })
      .then((result) => {
        metrics.step('rls_query');
        return writeAuditEvent(request.event);
      })
      .then(() => {
        timer.stop();
        
        metrics.histogram('auth.e2e.duration_ms', {
          value: performance.now() - startTime,
          tags: {
            success: 'true',
            trace_id: traceId,
          },
        });

        logger.info('Auth flow completed', { 
          traceId, 
          duration: performance.now() - startTime,
        });

        return result;
      })
      .catch((error) => {
        timer.stop();
        
        metrics.histogram('auth.e2e.duration_ms', {
          value: performance.now() - startTime,
          tags: {
            success: 'false',
            error: error.name,
          },
        });

        logger.error('Auth flow failed', { traceId, error });

        throw error;
      });
  });
}
```

---

## 6. Performance Test Scenarios

### 6.1 Token Validation Latency Test

```typescript
// test/performance/token-validation.latency.test.ts

describe('Token Validation Latency', () => {
  it('validates tokens within 50ms p95', async () => {
    const iterations = 1000;
    const durations: number[] = [];

    for (let i = 0; i < iterations; i++) {
      const token = generateValidToken();
      
      const start = performance.now();
      await validateTokenWithMetrics(token);
      const duration = performance.now() - start;
      
      durations.push(duration);
    }

    const p95 = calculateP95(durations);
    expect(p95).toBeLessThan(50);
  });

  it('handles JWKS cache hit efficiently', async () => {
    // Warm cache
    const token = generateValidToken();
    await validateTokenWithMetrics(token);

    // Measure cached validation
    const durations = [];
    for (let i = 0; i < 100; i++) {
      const start = performance.now();
      await validateTokenWithMetrics(token);
      durations.push(performance.now() - start);
    }

    const avg = calculateAverage(durations);
    expect(avg).toBeLessThan(10);
  });
});
```

### 6.2 Concurrent Session Test

```typescript
// test/performance/concurrent-sessions.test.ts

describe('Concurrent Session Limits', () => {
  it('enforces max concurrent sessions per user', async () => {
    const userId = 'test-user-001';
    const sessions = Array(10).fill(null).map(() => 
      authService.createSession(userId, 'tenant-001')
    );

    const results = await Promise.allSettled(sessions);
    const successes = results.filter(r => r.status === 'fulfilled');
    const failures = results.filter(r => r.status === 'rejected');

    expect(successes.length).toBeLessThanOrEqual(5);
    expect(failures.length).toBeGreaterThan(0);
  });

  it('measures session creation latency under load', async () => {
    const userId = 'test-user-001';
    const concurrency = 100;
    
    const start = performance.now();
    await Promise.all(
      Array(concurrency).fill(null).map(() => 
        authService.createSession(userId, 'tenant-001')
      )
    );
    const duration = performance.now() - start;

    const avgLatency = duration / concurrency;
    expect(avgLatency).toBeLessThan(100);
  });
});
```

### 6.3 RLS Query Performance Test

```typescript
// test/performance/rls-query.test.ts

describe('RLS Query Performance', () => {
  it('maintains query performance with RLS enabled', async () => {
    // Warm up
    await executeRLSQueryWithMetrics(
      'SELECT * FROM invoices WHERE tenant_id = $1',
      ['tenant-001']
    );

    const durations = [];
    for (let i = 0; i < 1000; i++) {
      const start = performance.now();
      await executeRLSQueryWithMetrics(
        'SELECT * FROM invoices WHERE tenant_id = $1 LIMIT 100',
        ['tenant-001']
      );
      durations.push(performance.now() - start);
    }

    const p95 = calculateP95(durations);
    expect(p95).toBeLessThan(100);
  });

  it('scales linearly with data volume', async () => {
    // Test with different data volumes
    const volumes = [100, 1000, 10000, 100000];
    const results = await Promise.all(
      volumes.map(async (volume) => {
        seedData('invoices', volume);
        
        const durations = [];
        for (let i = 0; i < 10; i++) {
          const start = performance.now();
          await executeRLSQueryWithMetrics(
            'SELECT * FROM invoices WHERE tenant_id = $1',
            ['tenant-001']
          );
          durations.push(performance.now() - start);
        }

        return {
          volume,
          avg: calculateAverage(durations),
        };
      })
    );

    // Verify linear scaling
    const scalingFactor = results[3].avg / results[0].avg;
    const volumeRatio = volumes[3] / volumes[0];
    
    expect(scalingFactor).toBeLessThan(volumeRatio * 2);
  });
});
```

### 6.4 Audit Log Write Performance Test

```typescript
// test/performance/audit-log-write.test.ts

describe('Audit Log Write Performance', () => {
  it('writes audit events within 20ms p95 (async)', async () => {
    const events = Array(1000).fill(null).map((_, i) => ({
      action: 'restricted.read',
      entityType: 'bank_credential',
      actorId: `user-${i}`,
      tenantId: 'tenant-001',
    }));

    const durations = await Promise.all(
      events.map(async (event) => {
        const start = performance.now();
        await writeAuditEventWithMetrics(event);
        return performance.now() - start;
      })
    );

    const p95 = calculateP95(durations);
    expect(p95).toBeLessThan(20);
  });

  it('handles concurrent writes without blocking', async () => {
    const concurrency = 100;
    
    const start = performance.now();
    await Promise.all(
      Array(concurrency).fill(null).map((_, i) => 
        writeAuditEventWithMetrics({
          action: 'restricted.read',
          entityType: 'bank_credential',
          actorId: `user-${i}`,
          tenantId: 'tenant-001',
        })
      )
    );
    const duration = performance.now() - start;

    // Should complete within 1 second for 100 concurrent writes
    expect(duration).toBeLessThan(1000);
  });
});
```

---

## 7. Load Testing Configuration

### 7.1 k6 Load Test Script

```javascript
// test/performance/k6-auth-flow.js

import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '1m', target: 100 },   // Ramp up
    { duration: '5m', target: 100 },   // Steady state
    { duration: '1m', target: 500 },   // Spike
    { duration: '5m', target: 500 },   // Sustained load
    { duration: '1m', target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function() {
  const token = getAuthToken();
  
  const res = http.get('https://api.example.com/auth/me', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });

  sleep(1);
}
```

### 7.2 Artillery Load Test Configuration

```yaml
# test/performance/artillery-config.yml

config:
  target: 'https://api.example.com'
  phases:
    - duration: 60
      arrivalRate: 10
    - duration: 300
      arrivalRate: 50
    - duration: 60
      arrivalRate: 100
  plugins:
    metrics-by-endpoint: {}
  
scenarios:
  - name: "Auth token validation"
    weight: 50
    flow:
      - get:
          url: "/auth/validate"
          headers:
            Authorization: "Bearer {{ $randomString() }}"
          expect:
            - statusCode: 200
            - maxResponseTime: 200
```

---

## 8. Performance Metrics Collection

### 8.1 Prometheus Metrics

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'auth-service'
    static_configs:
      - targets: ['auth-service:9090']
```

### 8.2 Key Performance Indicators

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Token validation p95 | < 50ms | > 100ms | > 200ms |
| MFA validation p95 | < 30ms | > 60ms | > 120ms |
| RLS query p95 | < 100ms | > 200ms | > 500ms |
| Audit log write p95 | < 20ms | > 40ms | > 100ms |
| Active sessions | < 90% capacity | > 90% | > 95% |
| Error rate | < 0.1% | > 0.5% | > 1% |

---

## 9. Performance Test Execution

### 9.1 Pre-Release Performance Gates

```bash
# Run performance tests before release
pnpm run test:performance:auth

# Check results
pnpm run test:performance:report
```

### 9.2 Performance Regression Detection

```bash
# Compare performance against baseline
pnpm run test:performance:compare --baseline=main
```

Results are stored in:

```
test/performance/results/
├── 2026-10-24-baseline.json
├── 2026-10-25-current.json
└── comparison-report.html
```

---

## 10. Monitoring and Alerting

### 10.1 Alert Rules

```yaml
# alerts/auth-performance.yml
groups:
  - name: auth_performance
    rules:
      - alert: AuthTokenValidationSlow
        expr: histogram_quantile(0.95, auth_token_validation_duration_seconds) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Auth token validation latency high"

      - alert: AuthErrorRateHigh
        expr: rate(auth_errors_total[5m]) / rate(auth_requests_total[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Auth error rate high"
```

---

*End of performance test hooks document.*
