package tenant

import (
	"context"
	"database/sql"
	"fmt"
	"log"
)

// RLSEnforcer applies tenant isolation via PostgreSQL SET LOCAL app.tenant_id.
type RLSEnforcer struct {
	db *sql.DB
}

// NewRLSEnforcer creates an RLS enforcer backed by a standard *sql.DB.
func NewRLSEnforcer(db *sql.DB) *RLSEnforcer {
	return &RLSEnforcer{db: db}
}

// SetTenantID executes SET LOCAL app.tenant_id within the current transaction.
// This is fail-closed: an empty tenant ID or execution error aborts the request.
func (r *RLSEnforcer) SetTenantID(ctx context.Context, tenantID string) error {
	if tenantID == "" {
		return fmt.Errorf("tenant_id must not be empty")
	}

	if err := ValidateBusinessID(tenantID); err != nil {
		return fmt.Errorf("invalid tenant_id: %w", err)
	}

	// SET LOCAL applies only within the current transaction.
	// The caller must wrap this in a transaction (BEGIN/COMMIT).
	_, err := r.db.ExecContext(ctx, "SET LOCAL app.tenant_id = $1", tenantID)
	if err != nil {
		log.Printf("RLS: failed to set app.tenant_id: %v", err)
		return fmt.Errorf("set app.tenant_id: %w", err)
	}

	log.Printf("RLS: tenant context set (id=%s)", tenantID)
	return nil
}

// CurrentTenantID retrieves the currently set app.tenant_id for diagnostics.
func (r *RLSEnforcer) CurrentTenantID(ctx context.Context) (string, error) {
	var tid string
	err := r.db.QueryRowContext(ctx, "SHOW app.tenant_id").Scan(&tid)
	if err != nil {
		return "", fmt.Errorf("query app.tenant_id: %w", err)
	}
	return tid, nil
}