package database

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/stdlib"
)

// DB wraps a pgx connection pool with tenant-scoped helpers.
type DB struct {
	pool *pgx.Pool
}

// New creates a connection pool from a DATABASE_URL.
func New(databaseURL string) (*DB, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	pool, err := pgx.NewPool(ctx, databaseURL)
	if err != nil {
		return nil, fmt.Errorf("connect to postgres: %w", err)
	}

	if err := pool.Ping(ctx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("ping postgres: %w", err)
	}

	log.Printf("database connection pool established")
	return &DB{pool: pool}, nil
}

// Close shuts down the connection pool.
func (db *DB) Close() {
	if db.pool != nil {
		db.pool.Close()
	}
}

// SetTenantID executes SET LOCAL app.tenant_id within a transaction or session.
// This enables PostgreSQL Row-Level Security (RLS) policies to filter by tenant.
func (db *DB) SetTenantID(ctx context.Context, tenantID string) error {
	if tenantID == "" {
		return fmt.Errorf("tenant_id must not be empty")
	}
	_, err := db.pool.Exec(ctx, "SET LOCAL app.tenant_id = $1", tenantID)
	return err
}

// Pool returns the underlying pgx pool for advanced operations.
func (db *DB) Pool() *pgx.Pool {
	return db.pool
}

// Stdlib returns a standard library-compatible DB for tools expecting *sql.DB.
func (db *DB) Stdlib() *stdlib.StdlibPool {
	return stdlib.NewPool(db.pool)
}