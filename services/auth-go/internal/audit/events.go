package audit

import "time"

// EventType represents the category of an audit event.
type EventType string

const (
	// EventLogin is emitted when a user successfully authenticates.
	EventLogin EventType = "login"
	// EventLogout is emitted when a user session is terminated.
	EventLogout EventType = "logout"
	// EventTokenRefresh is emitted when a token is refreshed.
	EventTokenRefresh EventType = "token_refresh"
	// EventMFAChallenge is emitted when an MFA challenge is issued or satisfied.
	EventMFAChallenge EventType = "mfa_challenge"
	// EventBusinessSwitch is emitted when a user switches business context.
	EventBusinessSwitch EventType = "business_switch"
	// EventTokenValidationFailure is emitted when token validation fails.
	EventTokenValidationFailure EventType = "token_validation_failure"
	// EventTenantAccessViolation is emitted when a tenant isolation check fails.
	EventTenantAccessViolation EventType = "tenant_access_violation"
)

// AuditEvent represents a single audit record written to the audit_log table.
type AuditEvent struct {
	ID            string    `json:"id"`
	Timestamp     time.Time `json:"ts"`
	EventType     EventType `json:"event_type"`
	TenantID      string    `json:"tenant_id"`
	UserIDHash    string    `json:"user_id_hash"`
	IP            string    `json:"ip"`
	UserAgent     string    `json:"user_agent"`
	RefusalReason string    `json:"refusal_reason,omitempty"`
	Success       bool      `json:"success"`
}