// Audit log writer (KB-016 / G17)
// Transactional insert with SET LOCAL app.business_id, redaction,
// and fail-closed error handling per docs/audit-log-security-review.md §2.3.

import { Client, type ClientConfig } from 'pg';
import { AuditEvent, AuditEventWrite } from './types.js';
import { redactEvent } from './redaction.js';

export class AuditLogWriteError extends Error {
  constructor(message: string, public readonly cause?: unknown) {
    super(message);
    this.name = 'AuditLogWriteError';
  }
}

type WriterOptions = {
  /** Optional static business_id to use when event payload does not carry one.
   *  For platform events this should be null/undefined. */
  defaultBusinessId?: string | null;
  /** Connection config for a new PG client per operation. If you need pooling,
   *  supply a factory rather than a config. For this task we stick with a fresh
   *  client per insert to keep the example simple. */
  pgConfig: ClientConfig;
};

export class AuditLogWriter {
  private readonly pgConfig: ClientConfig;
  private readonly defaultBusinessId?: string | null;

  constructor(opts: WriterOptions) {
    this.pgConfig = opts.pgConfig;
    this.defaultBusinessId = opts.defaultBusinessId ?? null;
  }

  /** Insert an audit event within a single transaction.
   *
   *  - Redacts the event before persisting.
   *  - Runs SET LOCAL app.business_id = ? as the first statement of the transaction.
   *    If business_id is null/undefined the setting is explicitly set to NULL
   *    (platform-scoped event). This keeps the RLS policy fail-closed.
   *  - On insert failure, throws AuditLogWriteError; caller decides fail-closed
   *    vs fail-open per docs/audit-log-security-review.md §2.3.
   */
  async insert({ business_id, event }: AuditEventWrite): Promise<void> {
    const client = new Client(this.pgConfig);
    await client.connect();
    try {
      await client.query('BEGIN');
      const bizId = business_id ?? this.defaultBusinessId ?? null;
      // SET LOCAL must be the first statement in the transaction.
      // Postgres does not support parameters in SET LOCAL; UUIDs are validated
      // by the caller and are safe to interpolate literally.
      // For platform-scoped events (bizId === null), we explicitly unset the GUC
      // so current_setting('app.business_id', true) returns NULL (fail-closed).
      if (bizId === null) {
        await client.query('SET LOCAL app.business_id = DEFAULT');
      } else {
        await client.query(`SET LOCAL app.business_id = '${bizId}'`);
      }

      const safe = redactEvent(event);
      const occurred = safe.occurred_at ?? new Date();
      await client.query(
        `INSERT INTO audit_log (
          business_id, occurred_at, actor_type, actor_id,
          event_type, entity_type, entity_id, outcome,
          metadata, ip_address, user_agent
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)`,
        [
          bizId,
          occurred,
          safe.actor_type,
          safe.actor_id,
          safe.event_type,
          safe.entity_type,
          safe.entity_id,
          safe.outcome,
          safe.metadata ?? {},
          safe.ip_address ?? null,
          safe.user_agent ?? null,
        ]
      );
      await client.query('COMMIT');
    } catch (e) {
      try { await client.query('ROLLBACK'); } catch {}
      throw new AuditLogWriteError('audit_log insert failed', e);
    } finally {
      await client.end();
    }
  }
}

/** Factory helper for tests / DI */
export function createWriter(pgConfig: ClientConfig, defaultBusinessId?: string | null) {
  return new AuditLogWriter({ pgConfig, defaultBusinessId });
}
