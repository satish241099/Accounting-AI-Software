package auth

import "fmt"

// MFAValidator enforces MFA claim requirements based on configuration.
type MFAValidator struct {
	enforced bool
}

// NewMFAValidator creates an MFA validator with the given enforcement flag.
func NewMFAValidator(enforced bool) *MFAValidator {
	return &MFAValidator{enforced: enforced}
}

// Validate checks whether the token's MFA claim satisfies the enforcement policy.
func (m *MFAValidator) Validate(claims *TokenClaims) error {
	if !m.enforced {
		return nil
	}
	if !claims.MFAEnforced {
		return fmt.Errorf("MFA enforcement required but token lacks MFA claim")
	}
	return nil
}

// IsEnforced returns whether MFA is enforced.
func (m *MFAValidator) IsEnforced() bool {
	return m.enforced
}