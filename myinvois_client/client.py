"""
Main MyInvois API client implementation.
"""

import logging
import time
from datetime import datetime

from .config import AWSSecretProvider, EnvironmentSecretProvider, MyInvoisConfig, SecretProvider
from .exceptions import (
    APIError,
    DocumentValidationError,
    DuplicateDocumentError,
    MyInvoisError,
    ValidationError,
)
from .http_client import MyInvoisHTTPClient
from .models import (
    ClassificationGate,
    DocumentStatus,
    DocumentStatusRequest,
    DocumentStatusResponse,
    DocumentSubmissionRequest,
    DocumentSubmissionResponse,
    DocumentType,
    DuplicateDocumentResponse,
    RefusalReason,
    TokenInfo,
    VerificationStatus,
)
from .security import SecurityLogger, TokenManager

# Configure logging
logger = logging.getLogger(__name__)


class MyInvoisClient:
    """
    Production-grade client for the MyInvois Intermediary API.

    Handles:
    - Login as Intermediary System authentication
    - Document submission with SHA-256 hashing
    - Document status polling
    - Duplicate detection
    - QR link generation
    - Certificate validation
    """

    def __init__(
        self,
        config: MyInvoisConfig,
        secret_provider: SecretProvider | None = None,
        environment: str = "production",
    ):
        """
        Initialize MyInvois client.

        Args:
            config: MyInvois configuration
            secret_provider: Secret provider (defaults to environment-based)
            environment: "production" or "preprod"
        """
        self.config = config
        self.environment = environment

        # Select base URL based on environment
        if environment == "preprod":
            self.base_url = config.api_preprod_base_url
        else:
            self.base_url = config.api_base_url

        # Use AWS secret provider if AWS credentials are available
        if config.aws_access_key_id and config.aws_secret_access_key:
            self.secret_provider = secret_provider or AWSSecretProvider(config)
        else:
            self.secret_provider = secret_provider or EnvironmentSecretProvider(config)

        # Initialize components
        self.http_client = MyInvoisHTTPClient(config, self.secret_provider)
        self.token_manager = TokenManager(config, self.http_client, self.secret_provider)
        self.security_logger = SecurityLogger()

        # Set default tenant context
        self.default_tenant_id = config.default_tenant_id

        # Validate configuration
        config.validate()

        logger.info(
            "MyInvois client initialized",
            extra={
                "environment": environment,
                "base_url": self.base_url,
                "max_document_size": config.max_document_size_bytes,
            },
        )

    def authenticate(self) -> TokenInfo:
        """
        Authenticate with the MyInvois API using Login as Intermediary System.

        Returns:
            TokenInfo object containing access token and expiry information.
        """
        return self.token_manager.get_access_token()

    def submit_document(self, request: DocumentSubmissionRequest) -> DocumentSubmissionResponse:
        """
        Submit a document to the MyInvois API.

        Args:
            request: Document submission request

        Returns:
            DocumentSubmissionResponse with submission details
        """
        try:
            # Validate document size before making any network calls
            request.validate_size(self.config.max_document_size_bytes)

            # Calculate document hash
            document_hash = request.calculate_hash()

            # Check for duplicate documents
            duplicate_check = self.check_duplicate_document(
                document_hash.hash_value, tenant_id=request.tenant_id or self.default_tenant_id
            )
            if duplicate_check.is_duplicate:
                raise DuplicateDocumentError(
                    "Duplicate document detected", document_uuid=duplicate_check.document_uuid
                )

            # Validate document type
            if not isinstance(request.document_type, DocumentType):
                raise DocumentValidationError(
                    f"Invalid document type: {request.document_type}",
                    document_hash=document_hash.hash_value,
                )

            # Submit document
            submission_payload = {
                "document_type": request.document_type.value,
                "document_data": request.document_data,
                "document_hash": document_hash.hash_value,
                "metadata": request.metadata or {},
                "tenant_id": request.tenant_id or self.default_tenant_id,
                "submission_timestamp": datetime.now().isoformat(),
            }

            response_data = self.http_client.post(
                f"{self.base_url}/api/v1.0/documents", data=submission_payload
            )

            # Parse response
            document_uuid = response_data.get("uuid", "")
            qr_link = response_data.get(
                "qr_link", f"https://myinvois.hasil.gov.my/qr/{document_uuid}"
            )
            status = DocumentStatus(response_data.get("status", "Submitted"))

            return DocumentSubmissionResponse(
                document_uuid=document_uuid,
                qr_link=qr_link,
                status=status,
                message=response_data.get("message"),
                document_hash=document_hash.hash_value,
                verification_status=VerificationStatus(
                    response_data.get("verification_status", "needs_verification")
                ),
                classification_gate=ClassificationGate(
                    response_data.get("classification_gate", "public")
                ),
                refusal_reason=(
                    RefusalReason(response_data["refusal_reason"])
                    if response_data.get("refusal_reason")
                    else None
                ),
            )

        except (DocumentValidationError, DuplicateDocumentError):
            raise
        except ValidationError as e:
            raise DocumentValidationError(
                f"Document validation failed: {str(e)}",
                document_hash=document_hash.hash_value if "document_hash" in locals() else None,
            ) from e
        except APIError as e:
            logger.error(
                "Document submission failed",
                extra={
                    "error_code": e.error_code,
                    "status_code": e.status_code,
                    "tenant_id": request.tenant_id or self.default_tenant_id,
                },
            )
            raise

    def check_duplicate_document(
        self, document_hash: str, tenant_id: str | None = None
    ) -> DuplicateDocumentResponse:
        """
        Check if a document is a duplicate.

        Args:
            document_hash: SHA-256 hash of the document
            tenant_id: Optional tenant identifier

        Returns:
            DuplicateDocumentResponse with duplicate information
        """
        try:
            response_data = self.http_client.get(
                f"{self.base_url}/api/v1.0/documents/duplicate-check",
                params={
                    "document_hash": document_hash,
                    "tenant_id": tenant_id or self.default_tenant_id,
                },
            )

            return DuplicateDocumentResponse(
                is_duplicate=response_data.get("is_duplicate", False),
                document_uuid=response_data.get("document_uuid"),
                duplicate_message=response_data.get("message"),
            )

        except APIError as e:
            logger.error(
                "Duplicate check failed",
                extra={
                    "error_code": e.error_code,
                    "status_code": e.status_code,
                    "tenant_id": tenant_id or self.default_tenant_id,
                },
            )
            raise

    def get_document_status(self, request: DocumentStatusRequest) -> DocumentStatusResponse:
        """
        Get the status of a submitted document.

        Args:
            request: Document status request

        Returns:
            DocumentStatusResponse with current status
        """
        try:
            response_data = self.http_client.get(
                f"{self.base_url}/api/v1.0/documents/{request.document_uuid}/status",
                params={"tenant_id": request.tenant_id or self.default_tenant_id},
            )

            return DocumentStatusResponse(
                document_uuid=request.document_uuid,
                status=DocumentStatus(response_data.get("status", "Submitted")),
                message=response_data.get("message"),
                verification_status=VerificationStatus(
                    response_data.get("verification_status", "needs_verification")
                ),
                classification_gate=ClassificationGate(
                    response_data.get("classification_gate", "public")
                ),
                document_hash=response_data.get("document_hash"),
                refusal_reason=(
                    RefusalReason(response_data["refusal_reason"])
                    if response_data.get("refusal_reason")
                    else None
                ),
                additional_info=response_data.get("additional_info", {}),
            )

        except APIError as e:
            logger.error(
                "Document status retrieval failed",
                extra={
                    "error_code": e.error_code,
                    "status_code": e.status_code,
                    "document_uuid": request.document_uuid,
                    "tenant_id": request.tenant_id or self.default_tenant_id,
                },
            )
            raise

    def wait_for_document_status(
        self,
        document_uuid: str,
        target_status: DocumentStatus,
        max_wait_seconds: int = 300,
        poll_interval_seconds: int = 5,
        tenant_id: str | None = None,
    ) -> DocumentStatusResponse:
        """
        Wait for a document to reach a specific status.

        Args:
            document_uuid: Document UUID
            target_status: Target status to wait for
            max_wait_seconds: Maximum time to wait
            poll_interval_seconds: Polling interval
            tenant_id: Optional tenant identifier

        Returns:
            DocumentStatusResponse when target status is reached
        """
        start_time = time.time()

        while time.time() - start_time < max_wait_seconds:
            status_response = self.get_document_status(
                DocumentStatusRequest(document_uuid=document_uuid, tenant_id=tenant_id)
            )

            if status_response.status == target_status:
                return status_response

            # If status is terminal (not the target), return immediately
            if status_response.status in [DocumentStatus.INVALID, DocumentStatus.CANCELLED]:
                return status_response

            time.sleep(poll_interval_seconds)

        raise MyInvoisError(
            f"Document did not reach status {target_status.value} within {max_wait_seconds} seconds",
            "TIMEOUT",
            {"document_uuid": document_uuid, "target_status": target_status.value},
        )

    def get_qr_link(self, document_uuid: str) -> str:
        """
        Get the QR link for a submitted document.

        Args:
            document_uuid: Document UUID

        Returns:
            QR link URL
        """
        return f"https://myinvois.hasil.gov.my/qr/{document_uuid}"

    def close(self) -> None:
        """Close the client and cleanup resources."""
        self.http_client.close()
        logger.info("MyInvois client closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
