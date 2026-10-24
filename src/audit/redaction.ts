// Defense-in-depth secret redaction for audit events (KB-016 / G17)
// Implements docs/audit-log-security-review.md §3.2 (whitelist, not blacklist)
// and §3.3 secret-material invariants.

import { AuditEvent, REDACTION_WHITELIST } from './types.js';

const SECRET_KEY_NAMES = new Set([
  'token', 'access_token', 'refresh_token', 'password', 'secret',
  'private_key', 'certificate', 'key', 'auth_token', 'bearer', 'api_key',
]);

// JWT header/payload pattern (eyJ...), PEM headers, and 16+ digit runs
const SECRET_PATTERNS: RegExp[] = [
  /^eyJ[\w-]+\.[\w-]+\.[\w-]+$/i,
  /^-----BEGIN [A-Z ]+-----/,
  /\b\d{16,}\b/,
];

function isSecretKeyName(k: string): boolean {
  const low = k.toLowerCase();
  for (const s of SECRET_KEY_NAMES) {
    if (low === s || low.endsWith('_' + s) || low.endsWith('-' + s)) return true;
  }
  return false;
}

function stripSecretPatterns(value: unknown): unknown {
  if (value == null) return value;
  if (typeof value === 'string') {
    if (SECRET_PATTERNS.some(p => p.test(value))) return '[REDACTED]';
    return value;
  }
  if (Array.isArray(value)) return value.map(stripSecretPatterns);
  if (typeof value === 'object') {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(value)) {
      if (isSecretKeyName(k)) continue;
      out[k] = stripSecretPatterns(v);
    }
    return out;
  }
  return value;
}

/** Whitelist fields per entity type. Anything not listed is dropped. */
function whitelistEvent(e: AuditEvent): AuditEvent {
  const whitelist = (REDACTION_WHITELIST as any)[e.entity_type];
  const allowed = whitelist ? new Set(whitelist) : null;

  if (!e.metadata) return e;
  if (!allowed) {
    // Unknown entity type: allow only safe top-level scalar fields explicitly permitted
    const sanitized: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(e.metadata)) {
      if (!isSecretKeyName(k)) sanitized[k] = stripSecretPatterns(v);
    }
    return { ...e, metadata: sanitized };
  }

  const filtered: Record<string, unknown> = {};
  for (const k of Object.keys(e.metadata)) {
    if (allowed.has(k)) {
      filtered[k] = stripSecretPatterns(e.metadata[k]);
    }
  }
  return { ...e, metadata: filtered };
}

/** Combined redaction: whitelist first, then defense-in-depth pattern strip. */
export function redactEvent(event: AuditEvent): AuditEvent {
  const whitelisted = whitelistEvent(event);
  // Redact metadata, and defensively strip any secret patterns in ip/user_agent
  const safe: AuditEvent = {
    ...whitelisted,
    metadata: stripSecretPatterns(whitelisted.metadata ?? {}) as Record<string, unknown>,
    ip_address: typeof whitelisted.ip_address === 'string' ? whitelisted.ip_address : undefined,
    user_agent: typeof whitelisted.user_agent === 'string' ? whitelisted.user_agent : undefined,
  };
  return safe;
}

/** Exposed for tests */
export { stripSecretPatterns, whitelistEvent };
