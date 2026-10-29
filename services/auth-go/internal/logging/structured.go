package logging

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"log"
	"os"
	"time"

	"github.com/google/uuid"

	"auth-go/internal/tenant"
)

// Logger emits structured JSON logs with correlation and tenant context.
type Logger struct {
	output *os.File
}

// New creates a structured logger writing to stdout.
func New() *Logger {
	return &Logger{output: os.Stdout}
}

// LogEntry represents a single structured log line.
type LogEntry struct {
	Timestamp    string `json:"ts"`
	Level        string `json:"level"`
	Message      string `json:"msg"`
	CorrelationID string `json:"correlation_id,omitempty"`
	TenantID     string `json:"tenant_id,omitempty"`
	UserIDHash   string `json:"user_id,omitempty"`
	EventType    string `json:"event_type"`
}

// Log writes a structured log entry.
func (l *Logger) Log(level, message, eventType string, ctx context.Context) {
	entry := LogEntry{
		Timestamp:  time.Now().UTC().Format(time.RFC3339),
		Level:      level,
		Message:    message,
		EventType:  eventType,
	}

	if cid, ok := tenant.FromContext(ctx); ok && cid != "" {
		entry.CorrelationID = cid
	}
	if tid, ok := tenant.FromContext(ctx); ok && tid != "" {
		entry.TenantID = tid
	}
	if uid, ok := tenant.FromContext(ctx); ok && uid != "" {
		entry.UserIDHash = hashString(uid)
	}

	// Simple JSON serialization (no external dependency)
	jsonLine := fmt.Sprintf(`{"ts":"%s","level":"%s","msg":"%s","event_type":"%s","correlation_id":"%s","tenant_id":"%s","user_id":"%s"}`,
		entry.Timestamp, entry.Level, entry.Message, entry.EventType,
		entry.CorrelationID, entry.TenantID, entry.UserIDHash)

	log.New(l.output, "", 0).Print(jsonLine)
}

// Info logs an informational message.
func (l *Logger) Info(message, eventType string, ctx context.Context) {
	l.Log("info", message, eventType, ctx)
}

// Error logs an error message.
func (l *Logger) Error(message, eventType string, ctx context.Context) {
	l.Log("error", message, eventType, ctx)
}

// Warn logs a warning message.
func (l *Logger) Warn(message, eventType string, ctx context.Context) {
	l.Log("warn", message, eventType, ctx)
}

// NewCorrelationID generates a UUID-based correlation ID.
func NewCorrelationID() string {
	return uuid.New().String()
}

// hashString returns the SHA-256 hex digest of a string.
func hashString(s string) string {
	h := sha256.Sum256([]byte(s))
	return hex.EncodeToString(h[:])
}

// Ensure fmt is imported.
import "fmt"