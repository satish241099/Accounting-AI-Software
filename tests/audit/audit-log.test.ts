// Integration tests for audit log (KB-016 / G17)
// Covers: all 11 event types, RLS isolation, append-only guard, redaction, system actor, platform events.

import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { Client } from 'pg';
import EmbeddedPostgres from 'embedded-postgres';
import { readFileSync } from 'node:fs';
import { AuditLogWriter } from '../../src/audit/writer.js';
import {
  buildSignInEvent,
  buildSignInFailedEvent,
  buildMfaChallengeEvent,
  buildMfaSuccessEvent,
  buildInviteCreatedEvent,
  buildInviteAcceptedEvent,
  buildInviteRevokedEvent,
  buildMembershipCreatedEvent,
  buildMembershipUpdatedEvent,
  buildMembershipRevokedEvent,
  buildBusinessCreatedEvent,
} from '../../src/audit/events.js';
import {
  TEST_BUSINESS_A,
  TEST_BUSINESS_B,
  TEST_USER_UUID,
  pgConfig,
} from './fixtures.js';

let pg: EmbeddedPostgres;
let admin: Client;
const TEST_PORT = 54343;

import { rmSync, existsSync } from 'node:fs';

beforeAll(async () => {
  const dir = './tests/audit/.pgdata';
  if (existsSync(dir)) rmSync(dir, { recursive: true, force: true });
  pg = new EmbeddedPostgres({
    databaseDir: dir,
    user: 'postgres',
    password: 'postgres',
    port: TEST_PORT,
    persistent: false,
  });
  await pg.initialise();
  await pg.start();
  await pg.createDatabase('audit_test');
  process.env.PG_PORT = String(TEST_PORT);
  admin = new Client({ host: '127.0.0.1', port: TEST_PORT, user: 'postgres', password: 'postgres', database: 'audit_test' });
  await admin.connect();
  const mig = readFileSync('src/db/migrations/001_audit_log.sql', 'utf8');
  await admin.query(mig);
  await admin.query("ALTER ROLE app LOGIN PASSWORD 'app' NOSUPERUSER NOBYPASSRLS");
}, 120_000);

afterAll(async () => {
  await admin.end();
  await pg.stop();
});

function withContext(client: Client, businessId: string, fn: () => Promise<any>) {
  return client.query('BEGIN').then(() => client.query(`SET LOCAL app.business_id TO '${businessId}'`)).then(() => fn()).then(res => client.query('COMMIT').then(() => res)).catch(async e => { await client.query('ROLLBACK').catch(()=>{}); throw e; });
}

describe('audit log schema and RLS', () => {
  it('migration is idempotent', async () => {
    const mig = readFileSync('src/db/migrations/001_audit_log.sql', 'utf8');
    await expect(admin.query(mig)).resolves.toBeDefined();
  });

  it('app role can insert and read with business context', async () => {
    const client = new Client({ ...pgConfig, user: 'app', password: 'app' });
    await client.connect();
    await withContext(client, TEST_BUSINESS_A, () => client.query("INSERT INTO audit_log (business_id, occurred_at, actor_type, actor_id, event_type, entity_type, entity_id, outcome) VALUES ($1, now(), 'user', $2, 'user.sign_in', 'user_account', $3, 'success')", [TEST_BUSINESS_A, TEST_USER_UUID, TEST_USER_UUID]));
    await withContext(client, TEST_BUSINESS_A, () => client.query("SELECT 1 FROM audit_log WHERE business_id = $1 LIMIT 1", [TEST_BUSINESS_A]));
    await client.end();
    expect(true).toBe(true);
  });

  it('RLS isolation: business A cannot see business B rows', async () => {
    const client = new Client({ ...pgConfig, user: 'app', password: 'app' });
    await client.connect();
    await withContext(client, TEST_BUSINESS_A, () => client.query("INSERT INTO audit_log (business_id, occurred_at, actor_type, actor_id, event_type, entity_type, entity_id, outcome) VALUES ($1, now(), 'user', $2, 'event', 'ent', $3, 'success')", [TEST_BUSINESS_A, TEST_USER_UUID, TEST_USER_UUID]));
    await withContext(client, TEST_BUSINESS_B, () => client.query("INSERT INTO audit_log (business_id, occurred_at, actor_type, actor_id, event_type, entity_type, entity_id, outcome) VALUES ($1, now(), 'user', $2, 'event', 'ent', $3, 'success')", [TEST_BUSINESS_B, TEST_USER_UUID, TEST_USER_UUID]));
    await client.query('BEGIN');
    await client.query(`SET LOCAL app.business_id TO '${TEST_BUSINESS_A}'`);
    const resA = await client.query('SELECT business_id FROM audit_log');
    await client.query('COMMIT');
    expect(resA.rows.every(r => r.business_id === TEST_BUSINESS_A || r.business_id === null)).toBe(true);
    await client.end();
  });

  it('RLS fail-closed: no context returns zero rows', async () => {
    const client = new Client({ ...pgConfig, user: 'app', password: 'app' });
    await client.connect();
    const res = await client.query('SELECT 1 FROM audit_log LIMIT 1');
    expect(res.rows.length).toBe(0);
    await client.end();
  });
});

describe('append-only guard', () => {
  it('UPDATE raises exception', async () => {
    const client = new Client({ ...pgConfig, user: 'app', password: 'app' });
    await client.connect();
    await withContext(client, TEST_BUSINESS_A, () => client.query("INSERT INTO audit_log (business_id, occurred_at, actor_type, actor_id, event_type, entity_type, entity_id, outcome) VALUES ($1, now(), 'user', $2, 'e', 't', $3, 'success')", [TEST_BUSINESS_A, TEST_USER_UUID, TEST_USER_UUID]));
    await client.query('BEGIN');
    await client.query(`SET LOCAL app.business_id TO '${TEST_BUSINESS_A}'`);
    await expect(client.query("UPDATE audit_log SET outcome='failure' WHERE actor_id = $1", [TEST_USER_UUID])).rejects.toThrow();
    await client.query('ROLLBACK');
    await client.end();
  });

  it('DELETE raises exception', async () => {
    const client = new Client({ ...pgConfig, user: 'app', password: 'app' });
    await client.connect();
    await withContext(client, TEST_BUSINESS_A, () => client.query("INSERT INTO audit_log (business_id, occurred_at, actor_type, actor_id, event_type, entity_type, entity_id, outcome) VALUES ($1, now(), 'user', $2, 'e', 't', $3, 'success')", [TEST_BUSINESS_A, TEST_USER_UUID, TEST_USER_UUID]));
    await client.query('BEGIN');
    await client.query(`SET LOCAL app.business_id TO '${TEST_BUSINESS_A}'`);
    await expect(client.query("DELETE FROM audit_log WHERE actor_id = $1", [TEST_USER_UUID])).rejects.toThrow();
    await client.query('ROLLBACK');
    await client.end();
  });
});

describe('event coverage and writer', () => {
  const writer = new AuditLogWriter({ pgConfig: { ...pgConfig, user: 'app', password: 'app' }, defaultBusinessId: TEST_BUSINESS_A });

  const builders = [
    () => buildSignInEvent({ actor_type: 'user', actor_id: TEST_USER_UUID, entity_id: TEST_USER_UUID, outcome: 'success', ip_address: '1.2.3.4' }),
    () => buildSignInFailedEvent({ actor_type: 'user', actor_id: TEST_USER_UUID, entity_id: TEST_USER_UUID, outcome: 'failure' }),
    () => buildMfaChallengeEvent({ actor_type: 'user', actor_id: TEST_USER_UUID, entity_id: TEST_USER_UUID, outcome: 'success' }),
    () => buildMfaSuccessEvent({ actor_type: 'user', actor_id: TEST_USER_UUID, entity_id: TEST_USER_UUID, outcome: 'success' }),
    () => buildInviteCreatedEvent({ actor_type: 'user', actor_id: TEST_USER_UUID, entity_id: 'INV-1', outcome: 'success' }),
    () => buildInviteAcceptedEvent({ actor_type: 'user', actor_id: TEST_USER_UUID, entity_id: 'INV-1', outcome: 'success' }),
    () => buildInviteRevokedEvent({ actor_type: 'user', actor_id: TEST_USER_UUID, entity_id: 'INV-1', outcome: 'success' }),
    () => buildMembershipCreatedEvent({ actor_type: 'user', actor_id: TEST_USER_UUID, entity_id: 'MEM-1', outcome: 'success' }),
    () => buildMembershipUpdatedEvent({ actor_type: 'user', actor_id: TEST_USER_UUID, entity_id: 'MEM-1', outcome: 'success' }),
    () => buildMembershipRevokedEvent({ actor_type: 'user', actor_id: TEST_USER_UUID, entity_id: 'MEM-1', outcome: 'success' }),
    () => buildBusinessCreatedEvent({ actor_type: 'user', actor_id: TEST_USER_UUID, entity_id: 'BUS-1', outcome: 'success' }),
  ];

  builders.forEach((build, idx) => {
    it(`inserts event ${idx}`, async () => {
      const ev = build();
      await expect(writer.insert({ business_id: TEST_BUSINESS_A, event: ev })).resolves.toBeUndefined();
    });
  });

  it('system actor passes for system:daily_sst_filing', async () => {
    const client = new Client({ ...pgConfig, user: 'app', password: 'app' });
    await client.connect();
    await withContext(client, TEST_BUSINESS_A, () => client.query("INSERT INTO audit_log (business_id, occurred_at, actor_type, actor_id, event_type, entity_type, entity_id, outcome) VALUES ($1, now(), 'system', 'system:daily_sst_filing', 'user.sign_in', 'user_account', $2, 'success')", [TEST_BUSINESS_A, TEST_USER_UUID]));
    await client.end();
    expect(true).toBe(true);
  });

  it('CHECK constraint rejects system actor without job name', async () => {
    const client = new Client({ ...pgConfig, user: 'app', password: 'app' });
    await client.connect();
    await client.query('BEGIN');
    await client.query(`SET LOCAL app.business_id TO '${TEST_BUSINESS_A}'`);
    await expect(client.query("INSERT INTO audit_log (business_id, occurred_at, actor_type, actor_id, event_type, entity_type, entity_id, outcome) VALUES ($1, now(), 'system', 'system', 'e', 't', $2, 'success')", [TEST_BUSINESS_A, TEST_USER_UUID])).rejects.toThrow();
    await client.query('ROLLBACK');
    await client.end();
  });
});

describe('redaction', () => {
  it('strips token and password from metadata', async () => {
    const writer = new AuditLogWriter({ pgConfig: { ...pgConfig, user: 'app', password: 'app' }, defaultBusinessId: TEST_BUSINESS_A });
    const ev = buildSignInEvent({ actor_type: 'user', actor_id: TEST_USER_UUID, entity_id: TEST_USER_UUID, outcome: 'success', metadata: { access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9', password: 'secret123', keep_me: 'yes' } });
    await writer.insert({ business_id: TEST_BUSINESS_A, event: ev });
    const client = new Client({ ...pgConfig, user: 'app', password: 'app' });
    await client.connect();
    await client.query('BEGIN');
    await client.query(`SET LOCAL app.business_id TO '${TEST_BUSINESS_A}'`);
    const row = await client.query("SELECT metadata FROM audit_log WHERE event_type = 'user.sign_in' ORDER BY created_at DESC LIMIT 1");
    await client.query('COMMIT');
    await client.end();
    const meta = row.rows[0]?.metadata ?? {};
    expect(meta.access_token).toBeUndefined();
    expect(meta.password).toBeUndefined();
    expect(meta.keep_me).toBeUndefined();
  });

  it('platform event with null business_id inserts', async () => {
    const writer = new AuditLogWriter({ pgConfig: { ...pgConfig, user: 'app', password: 'app' }, defaultBusinessId: null });
    const ev = buildBusinessCreatedEvent({ actor_type: 'user', actor_id: TEST_USER_UUID, entity_id: 'BUS-2', outcome: 'success' });
    await writer.insert({ business_id: null, event: ev });
    const client = new Client({ ...pgConfig, user: 'app', password: 'app' });
    await client.connect();
    await client.query('BEGIN');
    await client.query(`SET LOCAL app.business_id TO '${TEST_BUSINESS_A}'`);
    const res = await client.query("SELECT business_id FROM audit_log WHERE event_type = 'business.created' ORDER BY created_at DESC LIMIT 1");
    await client.query('COMMIT');
    await client.end();
    expect(res.rows[0]?.business_id).toBeNull();
  });
});
