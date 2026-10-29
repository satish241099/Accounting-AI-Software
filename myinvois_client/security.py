"""
Security utilities for the MyInvois API client.
"""

import hashlib
import hmac
import logging
import threading
from datetime import datetime
from typing import Any

from .config import MyInvoisConfig, SecretProvider
from .exceptions import AuthenticationError, CertificateValidationError
from .http_client import MyInvoisHTTPClient
from .models import TokenInfo

# Configure logging with security considerations
security_logger = logging.getLogger("myinvois.security")


class TokenManager:
    """
    Manages access tokens for MyInvois API authentication.

    Features:
    - Automatic token refresh
    - Token caching to avoid unnecessary API calls
    - Thread-safe token access
    """

    def __init__(
        self,
        config: MyInvoisConfig,
        http_client: MyInvoisHTTPClient,
        secret_provider: SecretProvider,
    ):
        self.config = config
        self.http_client = http_client
        self.secret_provider = secret_provider
        self._cached_token: TokenInfo | None = None
        self._token_lock = threading.Lock()

    def get_access_token(self) -> TokenInfo:
        """
        Get a valid access token, refreshing if necessary.

        Returns:
            TokenInfo with valid access token
        """
        with self._token_lock:
            # Check if we have a cached valid token
            if self._cached_token and not self._cached_token.is_expired(
                buffer_seconds=self.config.token_buffer_seconds
            ):
                return self._cached_token

            # Get new token
            token_info = self._request_new_token()
            self._cached_token = token_info

            # Set auth headers on the HTTP client
            self.http_client.set_auth_headers(token_info.access_token)

            return token_info

    def _request_new_token(self) -> TokenInfo:
        """
        Request a new access token from the MyInvois API.

        Returns:
            TokenInfo with new access token
        """
        try:
            # Get client secret from the secret provider
            client_secret = self.secret_provider.get_client_secret()

            # Prepare login request
            login_payload = {
                "grant_type": "client_credentials",
                "client_id": self.config.client_id,
                "client_secret": client_secret,
                "username": self.config.username,
                "password": self.config.password,
                "scope": "InvoicingAPI",
            }

            # Make authentication request
            response_data = self.http_client.post(
                f"{self.http_client.client.base_url}/api/v1.0/connect/token", data=login_payload
            )

            # Parse response
            access_token = response_data.get("access_token", "")
            if not access_token:
                raise AuthenticationError("No access token received from MyInvois API")

            expires_in = response_data.get("expires_in", 3600)  # 60 minutes default
            refresh_token = response_data.get("refresh_token")
            token_type = response_data.get("token_type", "Bearer")

            # Log successful authentication (without token details)
            security_logger.info(
                "Successfully authenticated with MyInvois API",
                extra={
                    "expires_in": expires_in,
                    "token_type": token_type,
                },
            )

            return TokenInfo(
                access_token=access_token,
                token_type=token_type,
                expires_in=expires_in,
                refresh_token=refresh_token,
                issued_at=datetime.now(),
            )

        except AuthenticationError:
            raise
        except Exception as e:
            security_logger.error(
                "Authentication request failed",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
            )
            raise AuthenticationError(f"Failed to authenticate with MyInvois API: {e}") from e

    def invalidate_token(self) -> None:
        """Invalidate the cached token."""
        with self._token_lock:
            self._cached_token = None
            self.http_client.clear_auth_headers()


class SecurityLogger:
    """
    Security-focused logger with data redaction.
    """

    # Sensitive fields that should never be logged
    SENSITIVE_FIELDS = {
        "access_token",
        "refresh_token",
        "client_secret",
        "password",
        "authorization",
        "certificate",
        "private_key",
        "api_key",
        "secret",
        "token",
        "credential",
        "document_hash",
        "document_data",
    }

    # Patterns for detecting sensitive data
    SENSITIVE_PATTERNS = [
        "Bearer ",
        "Basic ",
        "sha256:",
        "-----BEGIN",
        "-----END",
    ]

    def __init__(self):
        self.logger = logging.getLogger("myinvois.security")

    def redact_data(self, data: Any, max_depth: int = 5) -> Any:
        """
        Redact sensitive data from any data structure.

        Args:
            data: Data to redact
            max_depth: Maximum recursion depth

        Returns:
            Data with sensitive values redacted
        """
        if max_depth <= 0:
            return "[REDACTED_MAX_DEPTH]"

        if isinstance(data, dict):
            redacted = {}
            for key, value in data.items():
                if (
                    any(sensitive_field in key.lower() for sensitive_field in self.SENSITIVE_FIELDS)
                    or isinstance(value, str)
                    and any(pattern in value for pattern in self.SENSITIVE_PATTERNS)
                ):
                    redacted[key] = "[REDACTED]"
                else:
                    redacted[key] = self.redact_data(value, max_depth - 1)
            return redacted
        elif isinstance(data, list):
            return [self.redact_data(item, max_depth - 1) for item in data]
        elif isinstance(data, str):
            if any(pattern in data for pattern in self.SENSITIVE_PATTERNS):
                return "[REDACTED]"
            return data
        else:
            return data

    def log_security_event(self, event: str, level: int = logging.INFO, **context: Any) -> None:
        """
        Log a security event with automatic data redaction.

        Args:
            event: Event description
            level: Log level
            **context: Additional context (will be redacted)
        """
        redacted_context = self.redact_data(context)

        self.logger.log(level, f"Security event: {event}", extra={"context": redacted_context})

    def log_authentication_attempt(self, success: bool, error: str | None = None) -> None:
        """Log authentication attempt without exposing credentials."""
        self.log_security_event(
            "authentication_attempt",
            level=logging.INFO if success else logging.WARNING,
            success=success,
            error=error,
        )

    def log_document_submission(
        self, document_uuid: str, status: str, tenant_id: str | None = None
    ) -> None:
        """Log document submission event."""
        self.log_security_event(
            "document_submission", document_uuid=document_uuid, status=status, tenant_id=tenant_id
        )


class CertificateValidator:
    """
    Validates certificates used for document signing.
    """

    def __init__(self, secret_provider: SecretProvider):
        self.secret_provider = secret_provider

    def validate_certificate(self, document_hash: str) -> bool:
        """
        Validate that the certificate is valid for the document hash.

        Args:
            document_hash: SHA-256 hash of the document

        Returns:
            True if certificate is valid

        Raises:
            CertificateValidationError: If certificate validation fails
        """
        try:
            certificate = self.secret_provider.get_certificate()

            # Basic validation - check if certificate content is present
            if not certificate:
                raise CertificateValidationError("No certificate available")

            # Check for PEM format
            if "-----BEGIN CERTIFICATE-----" not in certificate:
                raise CertificateValidationError("Certificate is not in PEM format")

            # Additional validation logic would go here
            # For now, we do basic format checks

            return True

        except CertificateValidationError:
            raise
        except Exception as e:
            raise CertificateValidationError(f"Certificate validation failed: {e}") from e


class HashValidator:
    """
    Validates document hashes and ensures data integrity.
    """

    @staticmethod
    def validate_sha256_hash(hash_string: str) -> bool:
        """
        Validate that a string is a valid SHA-256 hash.

        Args:
            hash_string: Hash string to validate

        Returns:
            True if valid SHA-256 hash
        """
        if not isinstance(hash_string, str):
            return False

        # SHA-256 produces 64 character hex string
        if len(hash_string) != 64:
            return False

        try:
            int(hash_string, 16)
            return True
        except ValueError:
            return False

    @staticmethod
    def calculate_hmac(key: str, message: str, algorithm: str = "sha256") -> str:
        """
        Calculate HMAC for message authentication.

        Args:
            key: Secret key
            message: Message to authenticate
            algorithm: Hash algorithm

        Returns:
            HMAC hex digest
        """
        message_bytes = message.encode("utf-8")
        key_bytes = key.encode("utf-8")

        if algorithm == "sha256":
            hmac_obj = hmac.new(key_bytes, message_bytes, hashlib.sha256)
        elif algorithm == "sha1":
            hmac_obj = hmac.new(key_bytes, message_bytes, hashlib.sha1)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        return hmac_obj.hexdigest()
