package main

import (
	"database/sql"
	"log"
	"net/http"
	"os"
	"time"

	_ "github.com/jackc/pgx/v5/stdlib"

	"auth-go/internal/audit"
	"auth-go/internal/logging"
	"auth-go/pkg/api"
	"auth-go/pkg/config"
	"auth-go/pkg/database"
)

const version = "0.1.0"

func main() {
	cfg := config.Load()

	logger := logging.New()
	auditor := audit.NewWriter(nil) // Will be wired once DB is available

	// Connect to PostgreSQL if configured.
	var db *sql.DB
	if cfg.DatabaseURL != "" {
		pgdb, err := database.New(cfg.DatabaseURL)
		if err != nil {
			log.Fatalf("database connection failed: %v", err)
		}
		defer pgdb.Close()

		stdlibDB := pgdb.Stdlib()
		db = stdlibDB

		// Wire audit writer to the database.
		auditor = audit.NewWriter(db)

		// Run health check on startup.
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := pgdb.Ping(ctx); err != nil {
			log.Fatalf("database health check failed: %v", err)
		}
		log.Println("database health check passed")
	}

	handler := api.NewHandler(logger, auditor, version)

	routes := api.NewRouter(
		api.Route{Method: http.MethodGet, Path: "/health", Handler: handler.Health},
		api.Route{Method: http.MethodPost, Path: "/api/v1/auth/validate", Handler: handler.ValidateToken},
		api.Route{Method: http.MethodPost, Path: "/api/v1/audit/events", Handler: handler.WriteAuditEvent},
	)

	addr := ":" + cfg.Port
	log.Printf("auth-go service v%s starting on %s", version, addr)
	if err := http.ListenAndServe(addr, routes); err != nil {
		log.Fatalf("server failed: %v", err)
	}
}