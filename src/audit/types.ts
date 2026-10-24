// Audit event type definitions for KB-016 (G17)
// Implements the type contracts required by docs/audit-log-design.md
// and docs/audit-log-security-review.md (§3.2 whitelist, §3.3 invariants).
//
// The Multi-tenant Kernel & Authentication slice canonicalises the context GUC
// as app.business_id (vs app.tenant_id used in the ACCO-* firm-workspace slice).

export type AuditEventType =
  | 'user.sign_in'
  | 'user.sign_in_failed'
  | 'user.mfa_challenge'
  | 'user.mfa_success'
  | 'invite.created'
  | 'invite.accepted'
  | 'invite.revoked'
  | 'membership.created'
  | 'membership.updated'
  | 'membership.revoked'
  | 'business.created';

export type ActorType = 'user' | 'system';

export type Outcome = 'success' | 'failure';

export interface AuditMetadata {
  // Only whitelisted fields per entity type are permitted.
  // Anything not explicitly listed must be stripped by redaction.
  // Whitelist is enforced in src/audit/redaction.ts.
  [k: string]: unknown;
}

/** Immutable audit record shape that is written to audit_log. */
export interface AuditEvent {
  event_type: AuditEventType;
  actor_type: ActorType;
  /** For actor_type='user': UUID string. For 'system': 'system:<job>' */
  actor_id: string;
  entity_type: string;
  entity_id: string;
  outcome: Outcome;
  metadata?: AuditMetadata;
  ip_address?: string;
  user_agent?: string;
  occurred_at?: Date;
}

/** Payload for writer.insert — may carry optional business context for build-time convenience. */
export interface AuditEventWrite {
  business_id?: string | null;
  event: AuditEvent;
}

/** Redaction whitelist per entity type (docs/audit-log-security-review.md §3.2). */
export const REDACTION_WHITELIST = {
  user_account: ['user_id', 'display_name', 'email_domain'],
  invite: ['invite_id', 'invitee_email', 'inviter_user_id', 'status'],
  membership: ['user_id', 'business_id', 'role', 'status'],
  business: ['business_id', 'name', 'created_by_user_id'],
} as const;

export type EntityType = keyof typeof REDACTION_WHITELIST | string;
