package config

import (
	"os"
	"strconv"
)

// Config holds all environment-driven configuration for the auth-go service.
type Config struct {
	DatabaseURL       string
	EntraTenantID     string
	EntraClientID     string
	EntraClientSecret string
	EntraIssuerURL    string
	MFAClaimEnforced  bool
	LogLevel          string
	Port              string
	AllowedOrigins    string
}

// Load reads configuration from environment variables with sensible defaults.
func Load() *Config {
	return &Config{
		DatabaseURL:       getEnv("DATABASE_URL", ""),
		EntraTenantID:     getEnv("ENTRA_TENANT_ID", ""),
		EntraClientID:     getEnv("ENTRA_CLIENT_ID", ""),
		EntraClientSecret: getEnv("ENTRA_CLIENT_SECRET", ""),
		EntraIssuerURL:    getEnv("ENTRA_ISSUER_URL", ""),
		MFAClaimEnforced:  getEnvBool("MFA_CLAIM_ENFORCED", false),
		LogLevel:          getEnv("LOG_LEVEL", "info"),
		Port:              getEnv("PORT", "8080"),
		AllowedOrigins:    getEnv("ALLOWED_ORIGINS", "*"),
	}
}

func getEnv(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

func getEnvBool(key string, fallback bool) bool {
	if value := os.Getenv(key); value != "" {
		if b, err := strconv.ParseBool(value); err == nil {
			return b
		}
	}
	return fallback
}