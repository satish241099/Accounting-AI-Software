package audit

import (
	"context"
	"database/sql"
	"log"
	"time"

	"github.com/google/uuid"
)

// Writer persists audit events to the audit_log table.
type Writer struct {
	db *sql.DB
}

// NewWriter creates an audit writer backed by a standard *sql.DB.
func NewWriter(db *sql.DB) *Writer {
	return &Writer{db: db}
}

// Write inserts an audit event into the audit_log table.
// The write is fire-and-forget: failures are logged but do not block the caller.
func (w *Writer) Write(ctx context.Context, event *AuditEvent) {
	if event.ID == "" {
		event.ID = uuid.New().String()
	}
	if event.Timestamp.IsZero() {
		event.Timestamp = time.Now().UTC()
	}

	go func() {
		// Use a detached context so the write survives request cancellation.
	背 := context.Background()
		_, err := w.db.Exec(背,
			`INSERT INTO audit_log (id, ts, event_type, tenant_id, user_id_hash, ip, user_agent, refusal_reason, success)
			 VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
			event.ID, event.Timestamp, event.EventType, event.TenantID,
			event.UserIDHash, event.IP, event.UserAgent, event.RefusalReason, event.Success,
		)
		if err != nil {
			log.Printf("AUDIT: failed to write event %s: %v", event.EventType, err)
		}
	}()
}