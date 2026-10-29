"""
S3 Adapter for tenant-scoped document storage.

Enforces:
- ap-southeast-1 region residency (PDPA 2024 compliance)
- SHA-256 content-addressable keys for deduplication and integrity
- Tenant-scoped object keys preventing cross-tenant data access
- SSE-KMS encryption for all uploads
"""

import hashlib
import uuid
from dataclasses import dataclass
from typing import Optional

import boto3
from botocore.config import Config


@dataclass(frozen=True)
class UploadResult:
    """Result of a document upload operation."""

    object_key: str
    etag: str
    version_id: Optional[str]
    sha256_hash: str
    content_type: str
    size_bytes: int


@dataclass(frozen=True)
class DownloadResult:
    """Result of a document download operation."""

    content: bytes
    content_type: str
    metadata: dict


class S3AdapterError(Exception):
    """Base exception for S3 adapter errors."""

    pass


class RegionMismatchError(S3AdapterError):
    """Raised when S3 client is configured for a non-ap-southeast-1 region."""

    pass


class TenantScopeViolationError(S3AdapterError):
    """Raised when an operation attempts to access data outside the tenant's scope."""

    pass


class EncryptionRequiredError(S3AdapterError):
    """Raised when SSE-KMS encryption is not configured for upload."""

    pass


class S3Adapter:
    """
    Tenant-scoped S3 document storage adapter.

    All operations are scoped to a specific tenant to prevent cross-tenant data leakage.
    Object keys follow the format: `tenant/{tenant_id}/documents/{sha256_hash}`
    """

    REQUIRED_REGION = "ap-southeast-1"
    KEY_PREFIX = "tenant"

    def __init__(
        self,
        bucket_name: str,
        region: str = REQUIRED_REGION,
        kms_key_id: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ):
        """
        Initialize the S3 adapter.

        Args:
            bucket_name: S3 bucket name for document storage.
            region: AWS region. Must be 'ap-southeast-1' for PDPA compliance.
            kms_key_id: KMS key ID for SSE-KMS encryption. Required for production.
            endpoint_url: Optional custom endpoint URL (e.g., for LocalStack testing).

        Raises:
            RegionMismatchError: If region is not ap-southeast-1.
        """
        if region != self.REQUIRED_REGION:
            raise RegionMismatchError(
                f"Region must be '{self.REQUIRED_REGION}' for PDPA 2024 compliance. "
                f"Got: '{region}'"
            )

        self._bucket_name = bucket_name
        self._kms_key_id = kms_key_id

        # Configure boto3 client with retries and timeouts
        boto_config = Config(
            region_name=region,
            retries={"max_attempts": 3, "mode": "standard"},
            connect_timeout=30,
            read_timeout=60,
        )

        self._client = boto3.client(
            "s3",
            config=boto_config,
            endpoint_url=endpoint_url,
        )

        # Verify bucket exists and is accessible
        self._verify_bucket()

    def _verify_bucket(self) -> None:
        """Verify the bucket exists and is accessible."""
        try:
            self._client.head_bucket(Bucket=self._bucket_name)
        except self._client.exceptions.NoSuchBucket:
            raise S3AdapterError(f"Bucket '{self._bucket_name}' does not exist")
        except self._client.exceptions.ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            raise S3AdapterError(f"Cannot access bucket '{self._bucket_name}': {error_code}")

    @staticmethod
    def _compute_sha256(content: bytes) -> str:
        """Compute SHA-256 hash of content for content-addressable keys."""
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def _validate_tenant_id(tenant_id: uuid.UUID) -> str:
        """Validate and normalize tenant ID to string."""
        if not isinstance(tenant_id, uuid.UUID):
            raise TypeError(f"tenant_id must be a UUID, got {type(tenant_id).__name__}")
        return str(tenant_id)

    def generate_object_key(self, tenant_id: uuid.UUID, file_content: bytes) -> str:
        """
        Generate a tenant-scoped, content-addressable object key.

        Format: `tenant/{tenant_id}/documents/{sha256_hash}`

        Args:
            tenant_id: UUID identifying the tenant.
            file_content: File content bytes to hash.

        Returns:
            Object key string.
        """
        tenant_str = self._validate_tenant_id(tenant_id)
        sha256_hash = self._compute_sha256(file_content)
        return f"{self.KEY_PREFIX}/{tenant_str}/documents/{sha256_hash}"

    def _validate_tenant_scope(self, tenant_id: uuid.UUID, object_key: str) -> None:
        """
        Validate that an object key belongs to the specified tenant.

        Args:
            tenant_id: Expected tenant UUID.
            object_key: Object key to validate.

        Raises:
            TenantScopeViolationError: If object_key doesn't start with tenant prefix.
        """
        tenant_str = self._validate_tenant_id(tenant_id)
        expected_prefix = f"{self.KEY_PREFIX}/{tenant_str}/"
        if not object_key.startswith(expected_prefix):
            raise TenantScopeViolationError(
                f"Object key '{object_key}' does not belong to tenant '{tenant_str}'. "
                f"Expected prefix: '{expected_prefix}'"
            )

    def upload_document(
        self,
        tenant_id: uuid.UUID,
        file_content: bytes,
        content_type: str,
        metadata: Optional[dict] = None,
    ) -> UploadResult:
        """
        Upload a document to S3 with tenant-scoped key and SSE-KMS encryption.

        Args:
            tenant_id: UUID identifying the tenant.
            file_content: File content bytes.
            content_type: MIME type of the file.
            metadata: Optional user metadata to store with the object.

        Returns:
            UploadResult with object metadata.

        Raises:
            EncryptionRequiredError: If KMS key is not configured.
            TenantScopeViolationError: If key validation fails (internal error).
        """
        if not self._kms_key_id:
            raise EncryptionRequiredError(
                "SSE-KMS encryption required. Configure kms_key_id on S3Adapter initialization."
            )

        object_key = self.generate_object_key(tenant_id, file_content)
        sha256_hash = self._compute_sha256(file_content)

        # Prepare metadata with content hash for integrity verification
        s3_metadata = {
            "sha256": sha256_hash,
            "tenant_id": str(tenant_id),
            **(metadata or {}),
        }

        # Upload with SSE-KMS encryption
        response = self._client.put_object(
            Bucket=self._bucket_name,
            Key=object_key,
            Body=file_content,
            ContentType=content_type,
            Metadata=s3_metadata,
            ServerSideEncryption="aws:kms",
            SSEKMSKeyId=self._kms_key_id,
        )

        return UploadResult(
            object_key=object_key,
            etag=response.get("ETag", "").strip('"'),
            version_id=response.get("VersionId"),
            sha256_hash=sha256_hash,
            content_type=content_type,
            size_bytes=len(file_content),
        )

    def download_document(
        self, tenant_id: uuid.UUID, object_key: str
    ) -> DownloadResult:
        """
        Download a document from S3 with tenant scope validation.

        Args:
            tenant_id: UUID identifying the tenant.
            object_key: S3 object key to download.

        Returns:
            DownloadResult with content and metadata.

        Raises:
            TenantScopeViolationError: If object_key doesn't belong to tenant.
        """
        self._validate_tenant_scope(tenant_id, object_key)

        response = self._client.get_object(Bucket=self._bucket_name, Key=object_key)

        content = response["Body"].read()
        content_type = response.get("ContentType", "application/octet-stream")
        metadata = response.get("Metadata", {})

        # Verify content integrity via SHA-256 if present in metadata
        expected_hash = metadata.get("sha256")
        if expected_hash:
            actual_hash = self._compute_sha256(content)
            if actual_hash != expected_hash:
                raise S3AdapterError(
                    f"Content integrity check failed: expected SHA-256 {expected_hash}, "
                    f"got {actual_hash}"
                )

        return DownloadResult(
            content=content, content_type=content_type, metadata=metadata
        )

    def delete_document(self, tenant_id: uuid.UUID, object_key: str) -> None:
        """
        Delete a document from S3 with tenant scope validation.

        Args:
            tenant_id: UUID identifying the tenant.
            object_key: S3 object key to delete.

        Raises:
            TenantScopeViolationError: If object_key doesn't belong to tenant.
        """
        self._validate_tenant_scope(tenant_id, object_key)

        self._client.delete_object(Bucket=self._bucket_name, Key=object_key)

    def get_object_url(
        self, object_key: str, expires_in: int = 3600
    ) -> str:
        """
        Generate a pre-signed URL for object access.

        Args:
            object_key: S3 object key.
            expires_in: URL expiration time in seconds (default: 1 hour).

        Returns:
            Pre-signed URL string.
        """
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket_name, "Key": object_key},
            ExpiresIn=expires_in,
        )

    def object_exists(self, tenant_id: uuid.UUID, object_key: str) -> bool:
        """
        Check if an object exists with tenant scope validation.

        Args:
            tenant_id: UUID identifying the tenant.
            object_key: S3 object key to check.

        Returns:
            True if object exists, False otherwise.
        """
        self._validate_tenant_scope(tenant_id, object_key)

        try:
            self._client.head_object(Bucket=self._bucket_name, Key=object_key)
            return True
        except self._client.exceptions.ClientError as e:
            if e.response.get("Error", {}).get("Code") == "404":
                return False
            raise

    def get_object_metadata(self, tenant_id: uuid.UUID, object_key: str) -> dict:
        """
        Get object metadata without downloading content.

        Args:
            tenant_id: UUID identifying the tenant.
            object_key: S3 object key.

        Returns:
            Dictionary of object metadata.

        Raises:
            TenantScopeViolationError: If object_key doesn't belong to tenant.
        """
        self._validate_tenant_scope(tenant_id, object_key)

        response = self._client.head_object(Bucket=self._bucket_name, Key=object_key)
        return {
            "content_type": response.get("ContentType"),
            "content_length": response.get("ContentLength"),
            "etag": response.get("ETag", "").strip('"'),
            "last_modified": response.get("LastModified"),
            "metadata": response.get("Metadata", {}),
            "version_id": response.get("VersionId"),
        }