package api

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"time"

	"auth-go/internal/audit"
	"auth-go/internal/logging"
	"auth-go/internal/tenant"
)

// HealthResponse is the response from the /health endpoint.
type HealthResponse struct {
	Status    string `json:"status"`
	Timestamp string `json:"timestamp"`
	Version   string `json:"version"`
}

// TokenValidationRequest is the request body for token validation.
type TokenValidationRequest struct {
	Token string `json:"token"`
}

// TokenValidationResponse is the response for token validation.
type TokenValidationResponse struct {
	Valid       bool   `json:"valid"`
	BusinessID  string `json:"business_id,omitempty"`
	TenantID    string `json:"tenant_id,omitempty"`
	MFAEnforced bool   `json:"mfa_enforced"`
	Error       string `json:"error,omitempty"`
}

// ErrorResponse is a standard error response.
type ErrorResponse struct {
	Error   string `json:"error"`
	Details string `json:"details,omitempty"`
}

// Handler holds dependencies for HTTP handlers.
type Handler struct {
	logger   *logging.Logger
	auditor  *audit.Writer
	version  string
}

// NewHandler creates a new API handler.
func NewHandler(logger *logging.Logger, auditor *audit.Writer, version string) *Handler {
	return &Handler{
		logger:  logger,
		auditor: auditor,
		version: version,
	}
}

// Health handles GET /health.
func (h *Handler) Health(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		h.writeError(w, http.StatusMethodNotAllowed, "method not allowed", "")
		return
	}

	resp := HealthResponse{
		Status:    "ok",
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		Version:   h.version,
	}
	h.writeJSON(w, http.StatusOK, resp)
}

// ValidateToken handles POST /api/v1/auth/validate.
// Validates an Entra External ID token and returns the extracted claims.
func (h *Handler) ValidateToken(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		h.writeError(w, http.StatusMethodNotAllowed, "method not allowed", "")
		return
	}

	cid := tenant.NewCorrelationID()
	ctx := tenant.WithCorrelationID(r.Context(), cid)

	var req TokenValidationRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.writeError(w, http.StatusBadRequest, "invalid request body", err.Error())
		h.auditor.Write(ctx, &audit.AuditEvent{
			EventType: audit.EventTokenValidationFailure,
			Success:   false,
			RefusalReason: "malformed_request",
		})
		return
	}

	if req.Token == "" {
		h.writeError(w, http.StatusBadRequest, "token is required", "")
		h.auditor.Write(ctx, &audit.AuditEvent{
			EventType: audit.EventTokenValidationFailure,
			Success:   false,
			RefusalReason: "missing_token",
		})
		return
	}

	// Token validation logic would be invoked here via the auth.TokenValidator.
	// For now, return a placeholder response indicating the endpoint is operational.
	resp := TokenValidationResponse{
		Valid:       true,
		MFAEnforced: false,
	}

	h.logger.Info("token validated", "auth.validate", ctx)
	h.writeJSON(w, http.StatusOK, resp)
}

// WriteAuditEvent handles POST /api/v1/audit/events (internal endpoint).
func (h *Handler) WriteAuditEvent(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		h.writeError(w, http.StatusMethodNotAllowed, "method not allowed", "")
		return
	}

	var event audit.AuditEvent
	if err := json.NewDecoder(r.Body).Decode(&event); err != nil {
		h.writeError(w, http.StatusBadRequest, "invalid request body", err.Error())
		return
	}

	cid := tenant.NewCorrelationID()
	ctx := tenant.WithCorrelationID(r.Context(), cid)
	h.auditor.Write(ctx, &event)

	h.writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (h *Handler) writeJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(data); err != nil {
		log.Printf("failed to encode response: %v", err)
	}
}

func (h *Handler) writeError(w http.ResponseWriter, status int, message, details string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(ErrorResponse{Error: message, Details: details})
}