"""
Custom exceptions for the MyInvois Intermediary API Client.
"""

from typing import Any


class MyInvoisError(Exception):
    """Base exception for all MyInvois client errors."""

    def __init__(
        self, message: str, error_code: str | None = None, details: dict[str, Any] | None = None
    ):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class AuthenticationError(MyInvoisError):
    """Raised when authentication fails."""

    def __init__(self, message: str, token_info: dict[str, Any] | None = None):
        super().__init__(message, "AUTH_ERROR", token_info)


class ValidationError(MyInvoisError):
    """Raised when input validation fails."""

    def __init__(self, message: str, field_errors: dict[str, str] | None = None) -> None:
        super().__init__(message, "VALIDATION_ERROR", {"field_errors": field_errors or {}})


class APIError(MyInvoisError):
    """Raised when the MyInvois API returns an error response."""

    def __init__(self, message: str, status_code: int, response_data: dict[str, Any] | None = None):
        super().__init__(
            message, "API_ERROR", {"status_code": status_code, "response_data": response_data or {}}
        )
        self.status_code = status_code


class RateLimitError(MyInvoisError):
    """Raised when rate limits are exceeded."""

    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message, "RATE_LIMIT_ERROR", {"retry_after": str(retry_after) if retry_after else "unknown"})
        self.retry_after = retry_after


class DocumentValidationError(ValidationError):
    """Raised when document validation fails."""

    def __init__(
        self, message: str, document_hash: str | None = None, size_bytes: int | None = None
    ) -> None:
        details: dict[str, str] = {}
        if document_hash is not None:
            details["document_hash"] = document_hash
        if size_bytes is not None:
            details["size_bytes"] = str(size_bytes)
        super().__init__(message, details)


class DuplicateDocumentError(MyInvoisError):
    """Raised when duplicate document detection triggers."""

    def __init__(self, message: str, document_uuid: str | None = None) -> None:
        details: dict[str, str] = {}
        if document_uuid is not None:
            details["document_uuid"] = document_uuid
        super().__init__(message, "DUPLICATE_DOCUMENT_ERROR", details)


class CertificateValidationError(ValidationError):
    """Raised when certificate validation fails."""

    def __init__(self, message: str, certificate_details: dict[str, Any] | None = None) -> None:
        details: dict[str, str] = {}
        if certificate_details:
            # Store certificate_details as a string representation to avoid type issues
            import json
            details["certificate_details"] = json.dumps(certificate_details)
        super().__init__(message, details)
