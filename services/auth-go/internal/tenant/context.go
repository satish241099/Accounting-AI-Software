package tenant

import (
	"context"
	"errors"
	"fmt"
	"strings"
)

// ContextKey is the type for tenant-scoped values in context.Context.
type ContextKey string

const (
	// BusinessIDKey is the context key for the validated business (tenant) ID.
	BusinessIDKey ContextKey = "business_id"
	// CorrelationIDKey is the context key for request correlation ID.
	CorrelationIDKey ContextKey = "correlation_id"
	// UserIDKey is the context key for the authenticated user ID (hashed).
	UserIDKey ContextKey = "user_id"
)

// HeaderBusinessID is the HTTP header carrying the tenant identifier.
const HeaderBusinessID = "X-Business-Id"

// ValidateBusinessID checks that the business ID is a non-empty UUID-like string.
func ValidateBusinessID(bid string) error {
	if bid == "" {
		return errors.New("business id is required")
	}
	if len(bid) > 64 {
		return fmt.Errorf("business id too long: %d chars", len(bid))
	}
	// Allow alphanumeric, hyphens, underscores (UUID format or custom slug)
	for _, c := range bid {
		if !((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '-' || c == '_') {
			return fmt.Errorf("business id contains invalid character: %c", c)
		}
	}
	return nil
}

// NormalizeBusinessID trims whitespace and lowercases the business ID.
func NormalizeBusinessID(bid string) string {
	return strings.TrimSpace(bid)
}

// FromContext extracts the business ID from a context, if present.
func FromContext(ctx context.Context) (string, bool) {
	bid, ok := ctx.Value(BusinessIDKey).(string)
	return bid, ok
}

// WithBusinessID returns a context with the business ID set.
func WithBusinessID(ctx context.Context, bid string) context.Context {
	return context.WithValue(ctx, BusinessIDKey, bid)
}

// WithCorrelationID returns a context with the correlation ID set.
func WithCorrelationID(ctx context.Context, cid string) context.Context {
	return context.WithValue(ctx, CorrelationIDKey, cid)
}

// WithUserID returns a context with the (hashed) user ID set.
func WithUserID(ctx context.Context, uid string) context.Context {
	return context.WithValue(ctx, UserIDKey, uid)
}