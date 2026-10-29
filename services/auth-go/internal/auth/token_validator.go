package auth

import (
	"context"
	"crypto/rsa"
	"crypto/x509"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math"
	"math/big"
	"net/http"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

// TokenValidator validates Entra External ID OIDC tokens.
type TokenValidator struct {
	clientID     string
	tenantID     string
	issuer       string
	jwksURL      string
	httpClient   *http.Client
	knownKeys    map[string]*rsa.PublicKey
}

// TokenClaims represents the validated JWT claims from Entra External ID.
type TokenClaims struct {
	jwt.RegisteredClaims
	MFAEnforced bool   `json:"amr"`
	Email       string `json:"email"`
	Name        string `json:"name"`
	TenantID    string `json:"tid"`
	BusinessID  string `json:"bid"`
}

// NewTokenValidator creates a validator for a specific Entra tenant.
func NewTokenValidator(clientID, tenantID, issuer string, httpClient *http.Client) *TokenValidator {
	if httpClient == nil {
		httpClient = &http.Client{Timeout: 10 * time.Second}
	}

	jwksURL := fmt.Sprintf(
		"https://login.microsoftonline.com/%s/discovery/v2.0/keys",
		tenantID,
	)

	return &TokenValidator{
		clientID:  clientID,
		tenantID:  tenantID,
		issuer:    issuer,
		jwksURL:   jwksURL,
		httpClient: httpClient,
		knownKeys: make(map[string]*rsa.PublicKey),
	}
}

// Validate parses and validates a raw JWT token string.
func (v *TokenValidator) Validate(ctx context.Context, rawToken string) (*TokenClaims, error) {
	token, err := jwt.Parse(rawToken, v.keyFunc(), jwt.WithIssuer(v.issuer), jwt.WithAudience(v.clientID))
	if err != nil {
		return nil, fmt.Errorf("token parse: %w", err)
	}

	if !token.Valid {
		return nil, errors.New("token is invalid")
	}

	claims, ok := token.Claims.(*TokenClaims)
	if !ok {
		return nil, errors.New("unexpected claim type")
	}

	// Extract MFA enforcement from amr claim
	if amr, ok := token.Claims.(jwt.MapClaims); ok {
		if amrList, ok := amr["amr"].([]interface{}); ok {
			for _, m := range amrList {
				if mstr, ok := m.(string); ok && mstr == "mfa" {
					claims.MFAEnforced = true
					break
				}
			}
		}
	}

	return claims, nil
}

// keyFunc returns a function that resolves the signing key for a token.
func (v *TokenValidator) keyFunc() jwt.Keyfunc {
	return func(token *jwt.Token) (interface{}, error) {
		kid, ok := token.Header["kid"]
		if !ok {
			return nil, errors.New("missing kid in token header")
		}

		kidStr, ok := kid.(string)
		if !ok {
			return nil, errors.New("invalid kid type")
		}

		// Check cache first
		if key, ok := v.knownKeys[kidStr]; ok {
			return key, nil
		}

		// Fetch JWKS
		key, err := v.fetchJWKS(context.Background(), kidStr)
		if err != nil {
			return nil, fmt.Errorf("fetch JWKS for kid %s: %w", kidStr, err)
		}

		v.knownKeys[kidStr] = key
		return key, nil
	}
}

// jwksResponse represents the JWKS endpoint response.
type jwksResponse struct {
	Keys []json.RawMessage `json:"keys"`
}

// fetchJWKS retrieves a specific key from the JWKS endpoint.
func (v *TokenValidator) fetchJWKS(ctx context.Context, kid string) (*rsa.PublicKey, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", v.jwksURL, nil)
	if err != nil {
		return nil, fmt.Errorf("create JWKS request: %w", err)
	}

	resp, err := v.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("fetch JWKS: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read JWKS body: %w", err)
	}

	var jwks jwksResponse
	if err := json.Unmarshal(body, &jwks); err != nil {
		return nil, fmt.Errorf("parse JWKS: %w", err)
	}

	for _, rawKey := range jwks.Keys {
		var jwk struct {
			KID string `json:"kid"`
			N   string `json:"n"`
			E   string `json:"e"`
			KTY string `json:"kty"`
		}
		if err := json.Unmarshal(rawKey, &jwk); err != nil {
			continue
		}
		if jwk.KID != kid || jwk.KTY != "RSA" {
			continue
		}

		return parseRSAPublicKey(jwk.N, jwk.E)
	}

	return nil, fmt.Errorf("key %s not found in JWKS", kid)
}

// parseRSAPublicKey converts base64url-encoded modulus and exponent to an RSA key.
func parseRSAPublicKey(nB64, eB64 string) (*rsa.PublicKey, error) {
	nBytes, err := base64.RawURLEncoding.DecodeString(nB64)
	if err != nil {
		return nil, fmt.Errorf("decode n: %w", err)
	}
	eBytes, err := base64.RawURLEncoding.DecodeString(eB64)
	if err != nil {
		return nil, fmt.Errorf("decode e: %w", err)
	}

	n := new(big.Int).SetBytes(nBytes)
	e := int(new(big.Int).SetBytes(eBytes).Int64())

	return &rsa.PublicKey{N: n, E: e}, nil
}

// ExtractBusinessID retrieves the business identifier from claims.
func (c *TokenClaims) ExtractBusinessID() string {
	return c.BusinessID
}

// ExtractTenantID retrieves the Entra tenant identifier from claims.
func (c *TokenClaims) ExtractTenantID() string {
	return c.TenantID
}

// RequireMFA checks if MFA enforcement is required and was satisfied.
func (c *TokenClaims) RequireMFA(enforced bool) error {
	if !enforced {
		return nil
	}
	if !c.MFAEnforced {
		return errors.New("MFA claim required but not present in token")
	}
	return nil
}

// Ensure big is imported for parseRSAPublicKey.
import "math/big"