"""
Tests for S3 Adapter.

Tests cover:
- Tenant-scoped key generation
- SHA-256 content hashing
- ap-southeast-1 region enforcement
- Tenant scope validation on download/delete
- SSE-KMS encryption requirement
- Pre-signed URL generation
- Duplicate content handling
"""

import io
import uuid
from unittest.mock import MagicMock, patch

import pytest
import boto3
from botocore.exceptions import ClientError
from moto import mock_aws

# Import the classes we're testing
from src.kernel.storage.s3_adapter import (
    S3Adapter,
    S3AdapterError,
    RegionMismatchError,
    TenantScopeViolationError,
    EncryptionRequiredError,
    UploadResult,
)


@pytest.fixture
def sample_image_content():
    """Create a sample image for testing."""
    # Create a simple 10x10 red image
    from PIL import Image
    img = Image.new("RGB", (10, 10), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def sample_text_content():
    """Create sample text content for testing."""
    return b"Hello, Malaysia Accounting SaaS!"


@pytest.fixture
def tenant_id():
    """Provide a test tenant UUID."""
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def s3_adapter(sample_image_content):
    """Create an S3 adapter with a moto mock S3 bucket."""
    with mock_aws():
        # Create a test bucket
        client = boto3.client("s3", region_name="ap-southeast-1")
        client.create_bucket(
            Bucket="test-bucket",
            CreateBucketConfiguration={"LocationConstraint": "ap-southeast-1"}
        )

        adapter = S3Adapter(
            bucket_name="test-bucket",
            region="ap-southeast-1",
            kms_key_id="arn:aws:kms:ap-southeast-1:123456789012:key/test-key",
        )
        yield adapter


@pytest.fixture
def s3_adapter_no_kms(sample_image_content):
    """Create an S3 adapter without KMS key for encryption tests."""
    with mock_aws():
        client = boto3.client("s3", region_name="ap-southeast-1")
        client.create_bucket(
            Bucket="test-bucket-no-kms",
            CreateBucketConfiguration={"LocationConstraint": "ap-southeast-1"}
        )

        adapter = S3Adapter(
            bucket_name="test-bucket-no-kms",
            region="ap-southeast-1",
            # No kms_key_id
        )
        yield adapter


class TestRegionEnforcement:
    """Tests for region enforcement."""

    def test_rejects_non_southeast_region(self):
        """S3Adapter should reject regions other than ap-southeast-1."""
        with pytest.raises(RegionMismatchError) as exc_info:
            S3Adapter(
                bucket_name="test-bucket",
                region="us-east-1",
                kms_key_id="arn:aws:kms:us-east-1:123456789012:key/test-key",
            )
        assert "ap-southeast-1" in str(exc_info.value)

    def test_accepts_southeast_region(self):
        """S3Adapter should accept ap-southeast-1 region."""
        @mock_aws
        def _test():
            client = boto3.client("s3", region_name="ap-southeast-1")
            client.create_bucket(
                Bucket="test-bucket",
                CreateBucketConfiguration={"LocationConstraint": "ap-southeast-1"}
            )

            adapter = S3Adapter(
                bucket_name="test-bucket",
                region="ap-southeast-1",
                kms_key_id="arn:aws:kms:ap-southeast-1:123456789012:key/test-key",
            )
            assert adapter is not None

        _test()


class TestTenantScopedKeyGeneration:
    """Tests for tenant-scoped key generation."""

    def test_generates_tenant_scoped_key(self, s3_adapter, tenant_id, sample_image_content):
        """Key should be scoped to tenant."""
        key = s3_adapter.generate_object_key(tenant_id, sample_image_content)
        assert key.startswith(f"tenant/{tenant_id}/documents/")

    def test_different_tenants_get_different_keys(self, s3_adapter, sample_image_content):
        """Different tenants should get different keys for same content."""
        tenant1 = uuid.UUID("11111111-1111-1111-1111-111111111111")
        tenant2 = uuid.UUID("22222222-2222-2222-2222-222222222222")

        key1 = s3_adapter.generate_object_key(tenant1, sample_image_content)
        key2 = s3_adapter.generate_object_key(tenant2, sample_image_content)

        assert key1 != key2
        assert f"tenant/{tenant1}" in key1
        assert f"tenant/{tenant2}" in key2

    def test_same_content_same_key(self, s3_adapter, tenant_id):
        """Same content should produce same key (content-addressable)."""
        content = b"Same content for deduplication"
        key1 = s3_adapter.generate_object_key(tenant_id, content)
        key2 = s3_adapter.generate_object_key(tenant_id, content)
        assert key1 == key2

    def test_different_content_different_key(self, s3_adapter, tenant_id):
        """Different content should produce different keys."""
        content1 = b"Different content one"
        content2 = b"Different content two"
        key1 = s3_adapter.generate_object_key(tenant_id, content1)
        key2 = s3_adapter.generate_object_key(tenant_id, content2)
        assert key1 != key2

    def test_sha256_hash_matches_content(self, s3_adapter, tenant_id):
        """SHA-256 hash should match the content."""
        import hashlib
        content = b"Content for hash verification"
        expected_hash = hashlib.sha256(content).hexdigest()
        key = s3_adapter.generate_object_key(tenant_id, content)
        assert expected_hash in key


class TestUploadDocument:
    """Tests for document upload."""

    def test_upload_document(self, s3_adapter, tenant_id, sample_image_content):
        """Test successful document upload."""
        result = s3_adapter.upload_document(
            tenant_id=tenant_id,
            file_content=sample_image_content,
            content_type="image/png",
        )

        assert isinstance(result, UploadResult)
        assert result.object_key.startswith(f"tenant/{tenant_id}/documents/")
        assert result.sha256_hash
        assert result.content_type == "image/png"
        assert result.size_bytes == len(sample_image_content)

    def test_upload_with_metadata(self, s3_adapter, tenant_id, sample_image_content):
        """Test upload with custom metadata."""
        result = s3_adapter.upload_document(
            tenant_id=tenant_id,
            file_content=sample_image_content,
            content_type="image/png",
            metadata={"document_type": "receipt", "source": "email"},
        )

        assert isinstance(result, UploadResult)

    def test_upload_requires_kms(self, tenant_id, sample_image_content):
        """Upload should fail without KMS key configuration."""
        with mock_aws():
            client = boto3.client("s3", region_name="ap-southeast-1")
            client.create_bucket(
                Bucket="test-bucket-no-kms",
                CreateBucketConfiguration={"LocationConstraint": "ap-southeast-1"}
            )

            adapter = S3Adapter(
                bucket_name="test-bucket-no-kms",
                region="ap-southeast-1",
            )

            with pytest.raises(EncryptionRequiredError):
                adapter.upload_document(
                    tenant_id=tenant_id,
                    file_content=sample_image_content,
                    content_type="image/png",
                )

    def test_upload_invalid_tenant_type(self, s3_adapter):
        """Upload should fail with invalid tenant ID type."""
        with pytest.raises(TypeError):
            s3_adapter.upload_document(
                tenant_id="not-a-uuid",  # type: ignore
                file_content=b"content",
                content_type="text/plain",
            )


class TestDownloadDocument:
    """Tests for document download."""

    def test_download_document(self, s3_adapter, tenant_id, sample_image_content):
        """Test successful document download."""
        # Upload first
        upload_result = s3_adapter.upload_document(
            tenant_id=tenant_id,
            file_content=sample_image_content,
            content_type="image/png",
        )

        # Download
        result = s3_adapter.download_document(tenant_id, upload_result.object_key)

        assert result.content == sample_image_content
        assert result.content_type == "image/png"
        assert "sha256" in result.metadata
        assert result.metadata["sha256"] == upload_result.sha256_hash

    def test_download_tenant_mismatch(self, s3_adapter, sample_image_content):
        """Download should fail with wrong tenant ID."""
        tenant1 = uuid.UUID("11111111-1111-1111-1111-111111111111")
        tenant2 = uuid.UUID("22222222-2222-2222-2222-222222222222")

        # Upload with tenant1
        upload_result = s3_adapter.upload_document(
            tenant_id=tenant1,
            file_content=sample_image_content,
            content_type="image/png",
        )

        # Try to download with tenant2
        with pytest.raises(TenantScopeViolationError):
            s3_adapter.download_document(tenant2, upload_result.object_key)

    def test_download_missing_object(self, s3_adapter, tenant_id):
        """Download should raise error for missing object."""
        fake_key = f"tenant/{tenant_id}/documents/fakehash"
        with pytest.raises(ClientError):
            s3_adapter.download_document(tenant_id, fake_key)


class TestDeleteDocument:
    """Tests for document deletion."""

    def test_delete_document(self, s3_adapter, tenant_id, sample_image_content):
        """Test successful document deletion."""
        # Upload first
        upload_result = s3_adapter.upload_document(
            tenant_id=tenant_id,
            file_content=sample_image_content,
            content_type="image/png",
        )

        # Delete
        s3_adapter.delete_document(tenant_id, upload_result.object_key)

        # Verify deletion
        assert not s3_adapter.object_exists(tenant_id, upload_result.object_key)

    def test_delete_tenant_mismatch(self, s3_adapter, sample_image_content):
        """Delete should fail with wrong tenant ID."""
        tenant1 = uuid.UUID("11111111-1111-1111-1111-111111111111")
        tenant2 = uuid.UUID("22222222-2222-2222-2222-222222222222")

        # Upload with tenant1
        upload_result = s3_adapter.upload_document(
            tenant_id=tenant1,
            file_content=sample_image_content,
            content_type="image/png",
        )

        # Try to delete with tenant2
        with pytest.raises(TenantScopeViolationError):
            s3_adapter.delete_document(tenant2, upload_result.object_key)


class TestGetObjectUrl:
    """Tests for pre-signed URL generation."""

    def test_generate_presigned_url(self, s3_adapter, tenant_id, sample_image_content):
        """Test pre-signed URL generation."""
        upload_result = s3_adapter.upload_document(
            tenant_id=tenant_id,
            file_content=sample_image_content,
            content_type="image/png",
        )

        url = s3_adapter.get_object_url(upload_result.object_key, expires_in=3600)
        assert url.startswith("http")
        assert "Signature" in url

    def test_url_expiration(self, s3_adapter, tenant_id, sample_image_content):
        """Test URL expiration parameter."""
        upload_result = s3_adapter.upload_document(
            tenant_id=tenant_id,
            file_content=sample_image_content,
            content_type="image/png",
        )

        # 5 minute expiration
        url = s3_adapter.get_object_url(upload_result.object_key, expires_in=300)
        assert url.startswith("http")


class TestObjectExists:
    """Tests for existence checks."""

    def test_exists_after_upload(self, s3_adapter, tenant_id, sample_image_content):
        """Object should exist after upload."""
        upload_result = s3_adapter.upload_document(
            tenant_id=tenant_id,
            file_content=sample_image_content,
            content_type="image/png",
        )
        assert s3_adapter.object_exists(tenant_id, upload_result.object_key)

    def test_not_exists_before_upload(self, s3_adapter, tenant_id):
        """Object should not exist before upload."""
        fake_key = f"tenant/{tenant_id}/documents/nonexistent"
        assert not s3_adapter.object_exists(tenant_id, fake_key)

    def test_exists_tenant_mismatch(self, s3_adapter, sample_image_content):
        """Existence check should fail with wrong tenant."""
        tenant1 = uuid.UUID("11111111-1111-1111-1111-111111111111")
        tenant2 = uuid.UUID("22222222-2222-2222-2222-222222222222")

        upload_result = s3_adapter.upload_document(
            tenant_id=tenant1,
            file_content=sample_image_content,
            content_type="image/png",
        )

        # Check with wrong tenant should raise TenantScopeViolationError
        with pytest.raises(TenantScopeViolationError):
            s3_adapter.object_exists(tenant2, upload_result.object_key)


class TestGetObjectMetadata:
    """Tests for metadata retrieval."""

    def test_get_metadata(self, s3_adapter, tenant_id, sample_image_content):
        """Test metadata retrieval."""
        upload_result = s3_adapter.upload_document(
            tenant_id=tenant_id,
            file_content=sample_image_content,
            content_type="image/png",
            metadata={"custom_field": "custom_value"},
        )

        metadata = s3_adapter.get_object_metadata(tenant_id, upload_result.object_key)

        assert metadata["content_type"] == "image/png"
        assert metadata["content_length"] == len(sample_image_content)
        assert "sha256" in metadata["metadata"]
        # S3 lowercases metadata keys
        assert "custom-field" in metadata["metadata"]

    def test_metadata_tenant_mismatch(self, s3_adapter, sample_image_content):
        """Metadata retrieval should fail with wrong tenant."""
        tenant1 = uuid.UUID("11111111-1111-1111-1111-111111111111")
        tenant2 = uuid.UUID("22222222-2222-2222-2222-222222222222")

        upload_result = s3_adapter.upload_document(
            tenant_id=tenant1,
            file_content=sample_image_content,
            content_type="image/png",
        )

        with pytest.raises(TenantScopeViolationError):
            s3_adapter.get_object_metadata(tenant2, upload_result.object_key)


class TestContentIntegrity:
    """Tests for content integrity verification."""

    def test_integrity_check_passes(self, s3_adapter, tenant_id, sample_image_content):
        """Download should verify content integrity."""
        upload_result = s3_adapter.upload_document(
            tenant_id=tenant_id,
            file_content=sample_image_content,
            content_type="image/png",
        )

        result = s3_adapter.download_document(tenant_id, upload_result.object_key)
        assert result.content == sample_image_content
        assert result.metadata["sha256"] == upload_result.sha256_hash

    def test_tampered_content_detected(self, s3_adapter, tenant_id, sample_image_content):
        """Download should detect tampered content."""
        # Upload original
        upload_result = s3_adapter.upload_document(
            tenant_id=tenant_id,
            file_content=sample_image_content,
            content_type="image/png",
        )

        # Tamper with the object in S3 — moto doesn't re-compute metadata
        # so the SHA-256 stored in S3 object metadata remains the original hash.
        # To properly test tampering, we must also set the sha256 metadata
        # to the original hash while changing the body.
        tampered_content = sample_image_content + b"TAMPERED"
        original_hash = upload_result.sha256_hash
        tampered_client = boto3.client("s3", region_name="ap-southeast-1")
        tampered_client.put_object(
            Bucket="test-bucket",
            Key=upload_result.object_key,
            Body=tampered_content,
            Metadata={"sha256": original_hash},
        )

        # Download should detect mismatch
        with pytest.raises(S3AdapterError) as exc_info:
            s3_adapter.download_document(tenant_id, upload_result.object_key)
        assert "integrity check failed" in str(exc_info.value).lower()