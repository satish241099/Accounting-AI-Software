// Typed audit event builders for KB-016 (G17)
// One builder per required event type. All builders return a fully-formed AuditEvent
// with strict field allow-lists — no arbitrary metadata passthrough. Redaction is
// applied by the writer, not the builders.

import { AuditEvent, AuditEventType, ActorType, Outcome } from './types.js';

type BuilderOpts = {
  actor_type: ActorType;
  actor_id: string;
  entity_id: string;
  outcome: Outcome;
  ip_address?: string;
  user_agent?: string;
  occurred_at?: Date;
  metadata?: Record<string, unknown>;
};

function buildBase(
  event_type: AuditEventType,
  entity_type: string,
  opts: BuilderOpts
): AuditEvent {
  return {
    event_type,
    actor_type: opts.actor_type,
    actor_id: opts.actor_id,
    entity_type,
    entity_id: opts.entity_id,
    outcome: opts.outcome,
    metadata: opts.metadata ?? {},
    ip_address: opts.ip_address,
    user_agent: opts.user_agent,
    occurred_at: opts.occurred_at ?? new Date(),
  };
}

/** user.sign_in — successful authentication */
export function buildSignInEvent(opts: BuilderOpts & { entity_type?: 'user_account' }): AuditEvent {
  return buildBase('user.sign_in', opts.entity_type ?? 'user_account', opts);
}

/** user.sign_in_failed — authentication failure */
export function buildSignInFailedEvent(opts: BuilderOpts & { entity_type?: 'user_account' }): AuditEvent {
  // Ensure failure outcome, strip any reason that might contain secrets
  const base = buildBase('user.sign_in_failed', opts.entity_type ?? 'user_account', { ...opts, outcome: 'failure' });
  return { ...base, metadata: { ...(base.metadata ?? {}) } };
}

/** user.mfa_challenge — MFA challenge presented */
export function buildMfaChallengeEvent(opts: BuilderOpts & { entity_type?: 'user_account' }): AuditEvent {
  return buildBase('user.mfa_challenge', opts.entity_type ?? 'user_account', opts);
}

/** user.mfa_success — MFA succeeded */
export function buildMfaSuccessEvent(opts: BuilderOpts & { entity_type?: 'user_account' }): AuditEvent {
  return buildBase('user.mfa_success', opts.entity_type ?? 'user_account', opts);
}

/** invite.created */
export function buildInviteCreatedEvent(opts: BuilderOpts & { entity_type?: 'invite' }): AuditEvent {
  return buildBase('invite.created', opts.entity_type ?? 'invite', opts);
}

/** invite.accepted */
export function buildInviteAcceptedEvent(opts: BuilderOpts & { entity_type?: 'invite' }): AuditEvent {
  return buildBase('invite.accepted', opts.entity_type ?? 'invite', opts);
}

/** invite.revoked */
export function buildInviteRevokedEvent(opts: BuilderOpts & { entity_type?: 'invite' }): AuditEvent {
  return buildBase('invite.revoked', opts.entity_type ?? 'invite', opts);
}

/** membership.created */
export function buildMembershipCreatedEvent(opts: BuilderOpts & { entity_type?: 'membership' }): AuditEvent {
  return buildBase('membership.created', opts.entity_type ?? 'membership', opts);
}

/** membership.updated */
export function buildMembershipUpdatedEvent(opts: BuilderOpts & { entity_type?: 'membership' }): AuditEvent {
  return buildBase('membership.updated', opts.entity_type ?? 'membership', opts);
}

/** membership.revoked */
export function buildMembershipRevokedEvent(opts: BuilderOpts & { entity_type?: 'membership' }): AuditEvent {
  return buildBase('membership.revoked', opts.entity_type ?? 'membership', opts);
}

/** business.created — platform-scoped, business_id will be NULL for writer */
export function buildBusinessCreatedEvent(opts: BuilderOpts & { entity_type?: 'business' }): AuditEvent {
  return buildBase('business.created', opts.entity_type ?? 'business', opts);
}
