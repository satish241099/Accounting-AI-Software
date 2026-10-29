"""
Data models for the MyInvois Intermediary API Client.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from .exceptions import DocumentValidationError


class DocumentType(StrEnum):
    """Supported MyInvois document types."""

    INVOICE = "01"
    CREDIT_NOTE = "02"
    DEBIT_NOTE = "03"
    RECEIPT = "04"
    SELF_BILLED_INVOICE = "11"
    SELF_BILLED_CREDIT_NOTE = "12"
    SELF_BILLED_DEBIT_NOTE = "13"
    SELF_BILLED_RECEIPT = "14"


class DocumentStatus(StrEnum):
    """MyInvois document status values."""

    SUBMITTED = "Submitted"
    VALID = "Valid"
    INVALID = "Invalid"
    CANCELLED = "Cancelled"


class VerificationStatus(StrEnum):
    """Document verification status."""

    VERIFIED = "verified"
    NEEDS_VERIFICATION = "needs_verification"
    BLOCKED_SOURCE = "blocked_source"
    KNOWLEDGE_BASED = "knowledge_based"


class ClassificationGate(StrEnum):
    """Document classification gates."""

    PUBLIC = "public"
    RESTRICTED_REJECTED = "restricted_rejected"


class RefusalReason(StrEnum):
    """Refusal reasons for document processing."""

    NO_EVIDENCE = "no_evidence"
    BLOCKED_SOURCE = "blocked_source"
    RESTRICTED_CONTENT = "restricted_content"
    SCHEMA_VIOLATION = "schema_violation"
    CITATION_MISSING = "citation_missing"


@dataclass
class TokenInfo:
    """Access token information."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600  # 60 minutes in seconds
    refresh_token: str | None = None
    issued_at: datetime | None = field(default_factory=datetime.now)

    def is_expired(self, buffer_seconds: int = 60) -> bool:
        """Check if the token is expired or about to expire."""
        if not self.expires_in or self.issued_at is None:
            return True
        expiry_time = self.issued_at.timestamp() + self.expires_in - buffer_seconds
        return datetime.now().timestamp() > expiry_time


@dataclass
class LoginRequest:
    """Login as Intermediary System request."""

    client_id: str
    client_secret: str
    username: str
    password: str


@dataclass
class LoginResponse:
    """Login response from MyInvois API."""

    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str | None = None
    token_info: dict[str, Any] | None = field(default_factory=dict)


@dataclass
class DocumentHash:
    """Document hash and validation information."""

    hash_value: str
    algorithm: str = "SHA-256"
    calculated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_document(cls, document_data: str | dict[str, Any] | bytes) -> "DocumentHash":
        """Calculate SHA-256 hash from document data."""
        if isinstance(document_data, dict):
            # Sort keys to ensure consistent hashing
            json_str = json.dumps(document_data, sort_keys=True, separators=(",", ":"))
            data_bytes = json_str.encode("utf-8")
        elif isinstance(document_data, str):
            data_bytes = document_data.encode("utf-8")
        else:
            data_bytes = document_data

        hash_value = hashlib.sha256(data_bytes).hexdigest()
        return cls(hash_value=hash_value)


@dataclass
class DocumentSubmissionRequest:
    """Document submission request."""

    document_type: DocumentType
    document_data: str | dict[str, Any]
    qr_link_format: str = "https://myinvois.hasil.gov.my/qr/{document_uuid}"
    metadata: dict[str, Any] | None = field(default_factory=dict)
    tenant_id: str | None = None

    def validate_size(self, max_size_bytes: int = 300000) -> None:
        """Validate document size against MyInvois limits."""
        if isinstance(self.document_data, dict):
            json_str = json.dumps(self.document_data, separators=(",", ":"))
            size_bytes = len(json_str.encode("utf-8"))
        elif isinstance(self.document_data, str):
            size_bytes = len(self.document_data.encode("utf-8"))
        else:
            size_bytes = len(self.document_data)

        if size_bytes > max_size_bytes:
            raise DocumentValidationError(
                f"Document size {size_bytes} bytes exceeds MyInvois limit of {max_size_bytes} bytes",
                size_bytes=size_bytes,
            )

    def calculate_hash(self) -> DocumentHash:
        """Calculate document hash."""
        return DocumentHash.from_document(self.document_data)


@dataclass
class DocumentSubmissionResponse:
    """Document submission response."""

    document_uuid: str
    qr_link: str
    status: DocumentStatus
    message: str | None = None
    submission_timestamp: datetime = field(default_factory=datetime.now)
    verification_status: VerificationStatus = VerificationStatus.NEEDS_VERIFICATION
    classification_gate: ClassificationGate = ClassificationGate.PUBLIC
    document_hash: str | None = None
    refusal_reason: RefusalReason | None = None


@dataclass
class DocumentStatusRequest:
    """Document status request."""

    document_uuid: str
    tenant_id: str | None = None


@dataclass
class DocumentStatusResponse:
    """Document status response."""

    document_uuid: str
    status: DocumentStatus
    message: str | None = None
    status_timestamp: datetime = field(default_factory=datetime.now)
    verification_status: VerificationStatus = VerificationStatus.NEEDS_VERIFICATION
    classification_gate: ClassificationGate = ClassificationGate.PUBLIC
    document_hash: str | None = None
    refusal_reason: RefusalReason | None = None
    additional_info: dict[str, Any] | None = field(default_factory=dict)


@dataclass
class DuplicateDocumentResponse:
    """Duplicate document detection response."""

    is_duplicate: bool
    document_uuid: str | None = None
    duplicate_message: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
