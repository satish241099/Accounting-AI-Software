// Test fixtures and helpers for audit-log integration tests (KB-016)
// Uses a real PostgreSQL instance spun up via embedded-postgres in vitest setup.

import { randomUUID } from 'node:crypto';
import { Client, type ClientConfig } from 'pg';

export const TEST_BUSINESS_A = '11111111-1111-1111-1111-111111111111';
export const TEST_BUSINESS_B = '22222222-2222-2222-2222-222222222222';
export const TEST_USER_UUID = '33333333-3333-3333-3333-333333333333';

export const pgConfig: ClientConfig = {
  host: '127.0.0.1',
  port: Number(process.env.PG_PORT ?? 54343),
  user: process.env.PG_USER ?? 'postgres',
  password: process.env.PG_PASSWORD ?? 'postgres',
  database: process.env.PG_DATABASE ?? 'audit_test',
};

export async function withBusinessContext<T>(businessId: string | null, fn: () => Promise<T>): Promise<T> {
  const client = new Client(pgConfig);
  await client.connect();
  try {
    await client.query('BEGIN');
    if (businessId === null) {
      await client.query('SET LOCAL app.business_id = DEFAULT');
    } else {
      await client.query(`SET LOCAL app.business_id = '${businessId}'`);
    }
    // Run the fn via this client's connection? The fn uses AuditLogWriter which opens its own
    // connection. We rely on the GUC being set on our connection only. To keep tests simple
    // we emulate the context via a direct query for unit tests, but for writer tests we set
    // the GUC inside the writer itself.
    // This helper is primarily for RLS SELECT verification.
    const result = await fn();
    await client.query('COMMIT');
    return result;
  } finally {
    await client.end();
  }
}

export async function createTestEvent(client: Client, row: Partial<{
  business_id: string | null;
  event_type: string;
  actor_type: string;
  actor_id: string;
  outcome: string;
  entity_type: string;
  entity_id: string;
  metadata: any;
}>) {
  await client.query(
    `INSERT INTO audit_log (
      business_id, occurred_at, actor_type, actor_id,
      event_type, entity_type, entity_id, outcome, metadata
    ) VALUES ($1, now(), $2, $3, $4, $5, $6, $7, $8)`,
    [
      row.business_id ?? null,
      row.actor_type ?? 'user',
      row.actor_id ?? TEST_USER_UUID,
      row.event_type ?? 'user.sign_in',
      row.entity_type ?? 'user_account',
      row.entity_id ?? randomUUID(),
      row.outcome ?? 'success',
      row.metadata ?? {},
    ]
  );
}

export async function countRows(client: Client, businessId?: string | null) {
  const q = businessId === undefined
    ? 'SELECT count(*)::int AS n FROM audit_log'
    : 'SELECT count(*)::int AS n FROM audit_log WHERE business_id = $1 OR business_id IS NULL';
  const res = await client.query(q, businessId === undefined ? [] : [businessId]);
  return Number(res.rows[0].n);
}
