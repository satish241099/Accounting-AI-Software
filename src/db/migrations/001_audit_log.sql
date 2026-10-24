-- Migration 001_audit_log — audit_log table (G17 / KB-016)
--
-- Versioned migration guarded by the schema_migrations table and a transactional
-- advisory lock so concurrent migrators cannot apply it twice. Self-contained:
-- carries the full DDL from src/db/schema/audit_log.sql so a fresh database can be
-- brought up by applying the migrations directory alone.
--
-- Idempotency: the guard row makes re-running a no-op; every DDL statement inside
-- also uses IF NOT EXISTS / DROP-then-CREATE so a crashed first attempt (marker not
-- yet written, DDL partially applied) can be safely re-applied.

BEGIN;

SELECT pg_advisory_xact_lock(hashtext('migration:001_audit_log'));

CREATE TABLE IF NOT EXISTS schema_migrations (
    version    VARCHAR(128) PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

DO $migration$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM schema_migrations WHERE version = '001_audit_log') THEN

    -- ---- Roles -------------------------------------------------------------
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'migrator') THEN
      CREATE ROLE migrator NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app') THEN
      CREATE ROLE app NOLOGIN;
    END IF;

    -- ---- Table -------------------------------------------------------------
    CREATE TABLE IF NOT EXISTS audit_log (
        id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        business_id UUID,
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

    -- ---- Indexes -----------------------------------------------------------
    CREATE INDEX IF NOT EXISTS idx_audit_log_business_occurred
      ON audit_log (business_id, occurred_at DESC);
    CREATE INDEX IF NOT EXISTS idx_audit_log_event_type_occurred
      ON audit_log (event_type, occurred_at DESC);
    CREATE INDEX IF NOT EXISTS idx_audit_log_entity_occurred
      ON audit_log (entity_type, entity_id, occurred_at DESC);

    -- ---- Append-only guard -------------------------------------------------
    CREATE OR REPLACE FUNCTION audit_log_append_only() RETURNS trigger AS $append_only_fn$
    BEGIN
      RAISE EXCEPTION 'audit_log is append-only (attempted %)', TG_OP
        USING ERRCODE = 'restrict_violation';
    END;
    $append_only_fn$ LANGUAGE plpgsql;

    DROP TRIGGER IF EXISTS audit_log_no_update_or_delete ON audit_log;
    CREATE TRIGGER audit_log_no_update_or_delete
      BEFORE UPDATE OR DELETE ON audit_log
      FOR EACH ROW EXECUTE FUNCTION audit_log_append_only();

    -- ---- RLS ---------------------------------------------------------------
    ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
    ALTER TABLE audit_log FORCE ROW LEVEL SECURITY;

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

    -- ---- Grants ------------------------------------------------------------
    REVOKE ALL ON audit_log FROM PUBLIC;
    REVOKE UPDATE, DELETE ON audit_log FROM app;
    GRANT SELECT, INSERT ON audit_log TO app;
    GRANT SELECT ON audit_log TO migrator;

    INSERT INTO schema_migrations (version, applied_at) VALUES ('001_audit_log', now());
  END IF;
END
$migration$;

COMMIT;
