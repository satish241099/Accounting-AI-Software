-- audit_log — immutable audit trail for authentication and membership events (G17 / KB-016)
--
-- Canonical carrier for the Multi-tenant Kernel & Authentication slice (feature F-MVKTMUSS-001D-92EB).
-- Design basis: docs/audit-log-design.md (§1 canonical schema), docs/audit-log-security-review.md
-- (§3.2 whitelist redaction, §3.3 secret invariants), docs/audit-log-db-notes.md (§1.2 correction 2:
-- append-only enforced by the database, not by convention), docs/db-contracts.md Part 2 (fail-closed
-- RLS contract, `SET LOCAL app.business_id`, role split).
--
-- Slice-level notes (KB-016):
--   * Partition key is `business_id` (the Multi-tenant Kernel slice canonicalises the
--     `app.business_id` context GUC; the Firm Beachhead ACCO-* tables use `app.tenant_id`).
--   * `business_id` is NULLABLE: platform-scoped events (sign-in, failed sign-in, business
--     creation before a membership exists) have no business context yet. The RLS policy is
--     deliberately `business_id IS NULL OR business_id = current_setting(...)` so platform
--     rows remain insertable/readable while tenant-scoped rows fail closed without context.
--   * This is the G17 subset: events + append-only + redaction. No hash chain, no S3 export,
--     no legal hold (ACCO-018 scope).

BEGIN;

-- ---- Roles -------------------------------------------------------------------
-- Idempotent role bootstrap. The migrator owns the table; the app role gets
-- INSERT + SELECT only. Neither role has BYPASSRLS or SUPERUSER.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'migrator') THEN
    CREATE ROLE migrator NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app') THEN
    CREATE ROLE app NOLOGIN;
  END IF;
END;
$$;

-- ---- Table -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_log (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID,                          -- NULL = platform-scoped event (no business context yet)
    occurred_at TIMESTAMPTZ NOT NULL,
    actor_type  VARCHAR(20) NOT NULL,
    actor_id    VARCHAR(128) NOT NULL,
    event_type  VARCHAR(40) NOT NULL,
    entity_type VARCHAR(40) NOT NULL,
    entity_id   VARCHAR(128) NOT NULL,
    outcome     VARCHAR(20) NOT NULL,
    metadata    JSONB,
    ip_address  INET,
    user_agent  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Actor identity invariant (KB-016 contract):
    --   * user actors carry a UUID id
    --   * system actors carry the job-scoped form 'system:<job>' (never bare 'system',
    --     never a user token)
    CONSTRAINT audit_log_actor_shape CHECK (
      (actor_type = 'user'   AND actor_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
      OR
      (actor_type = 'system' AND actor_id ~ '^system:.+$')
    ),
    CONSTRAINT audit_log_outcome CHECK (outcome IN ('success', 'failure')),
    CONSTRAINT audit_log_actor_type CHECK (actor_type IN ('user', 'system'))
);

COMMENT ON TABLE audit_log IS
  'Append-only audit trail for auth/membership events (G17). No UPDATE/DELETE permitted. Never store tokens, passwords, certificates, or secret material in metadata.';

COMMENT ON COLUMN audit_log.business_id IS
  'Business workspace the event belongs to; NULL for platform-scoped events (sign-in, failed sign-in, business creation before membership).';

COMMENT ON COLUMN audit_log.actor_id IS
  'User UUID for actor_type=''user''; job-scoped identifier ''system:<job>'' for actor_type=''system''.';

-- ---- Indexes -----------------------------------------------------------------
-- Primary query patterns: per-business timeline, per-event-type forensics,
-- per-entity history.
CREATE INDEX IF NOT EXISTS idx_audit_log_business_occurred
  ON audit_log (business_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_event_type_occurred
  ON audit_log (event_type, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity_occurred
  ON audit_log (entity_type, entity_id, occurred_at DESC);

-- ---- Append-only guard (docs/audit-log-db-notes.md §1.2 correction 2) --------
CREATE OR REPLACE FUNCTION audit_log_append_only() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'audit_log is append-only (attempted %)', TG_OP
    USING ERRCODE = 'restrict_violation';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS audit_log_no_update_or_delete ON audit_log;
CREATE TRIGGER audit_log_no_update_or_delete
  BEFORE UPDATE OR DELETE ON audit_log
  FOR EACH ROW EXECUTE FUNCTION audit_log_append_only();

-- ---- RLS: fail-closed tenant isolation (docs/db-contracts.md Part 2) ---------
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log FORCE ROW LEVEL SECURITY;

-- Single fail-closed policy for reads and writes. current_setting(..., true) returns
-- NULL when the context was never set, and '' on a pooled session whose previous
-- transaction used SET LOCAL and committed (Postgres leaves the GUC defined but
-- empty). NULLIF(..., '')::uuid normalises both to NULL so:
--   * tenant-scoped rows are invisible and unwritable without business context
--     (NULL = business_id is not true — fail-closed, and never a cast error),
--   * platform-scoped rows (business_id IS NULL) remain insertable and readable,
--     because the first disjunct is satisfied by the row itself.
DROP POLICY IF EXISTS audit_log_business_isolation ON audit_log;
CREATE POLICY audit_log_business_isolation ON audit_log
  USING (
    business_id IS NULL
    OR business_id = NULLIF(current_setting('app.business_id', true), '')::uuid
  )
  WITH CHECK (
    business_id IS NULL
    OR business_id = NULLIF(current_setting('app.business_id', true), '')::uuid
  );

-- ---- Grants: INSERT + SELECT only -------------------------------------------
REVOKE ALL ON audit_log FROM PUBLIC;
REVOKE UPDATE, DELETE ON audit_log FROM app;
GRANT SELECT, INSERT ON audit_log TO app;
GRANT SELECT ON audit_log TO migrator;

COMMIT;
