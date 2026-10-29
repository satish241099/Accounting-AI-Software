"""
Tests for the MyInvois Intermediary API Client.
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from myinvois_client.client import MyInvoisClient
from myinvois_client.config import MyInvoisConfig
from myinvois_client.exceptions import (
    APIError,
    AuthenticationError,
    DocumentValidationError,
    MyInvoisError,
    RateLimitError,
    ValidationError,
)
from myinvois_client.models import (
    DocumentHash,
    DocumentStatus,
    DocumentStatusRequest,
    DocumentSubmissionRequest,
    DocumentType,
    DuplicateDocumentResponse,
    TokenInfo,
)
from myinvois_client.security import (
    HashValidator,
    SecurityLogger,
)
from myinvois_client.utils import (
    format_currency_malaysia,
    format_datetime,
    is_valid_malaysian_tin,
    mask_sensitive_string,
    normalize_phone_number_malaysia,
    parse_datetime,
    validate_document_status,
    validate_document_type,
    validate_uuid,
)


class TestModels:
    """Test data models."""

    def test_document_type_enum(self):
        """Test document type enum values."""
        assert DocumentType.INVOICE == "01"
        assert DocumentType.CREDIT_NOTE == "02"
        assert DocumentType.DEBIT_NOTE == "03"
        assert DocumentType.RECEIPT == "04"
        assert DocumentType.SELF_BILLED_INVOICE == "11"
        assert DocumentType.SELF_BILLED_CREDIT_NOTE == "12"
        assert DocumentType.SELF_BILLED_DEBIT_NOTE == "13"
        assert DocumentType.SELF_BILLED_RECEIPT == "14"

    def test_document_status_enum(self):
        """Test document status enum values."""
        assert DocumentStatus.SUBMITTED == "Submitted"
        assert DocumentStatus.VALID == "Valid"
        assert DocumentStatus.INVALID == "Invalid"
        assert DocumentStatus.CANCELLED == "Cancelled"

    def test_token_info_expiry(self):
        """Test token expiry checking."""
        # Create token that expires in 1 hour
        token = TokenInfo(access_token="test_token", expires_in=3600, issued_at=datetime.now())
        assert not token.is_expired()

        # Create token that expires in 30 seconds (with 60 second buffer)
        token = TokenInfo(access_token="test_token", expires_in=30, issued_at=datetime.now())
        assert token.is_expired(buffer_seconds=60)

    def test_document_hash_calculation(self):
        """Test document hash calculation."""
        # Test with string data
        doc_hash = DocumentHash.from_document("test document")
        assert doc_hash.hash_value is not None
        assert len(doc_hash.hash_value) == 64  # SHA-256 hex length

        # Test with dict data
        doc_data = {"key": "value", "number": 123}
        doc_hash = DocumentHash.from_document(doc_data)
        assert doc_hash.hash_value is not None
        assert len(doc_hash.hash_value) == 64

        # Test hash consistency (same input should give same output)
        hash1 = DocumentHash.from_document(doc_data)
        hash2 = DocumentHash.from_document(doc_data)
        assert hash1.hash_value == hash2.hash_value

    def test_document_size_validation(self):
        """Test document size validation."""
        # Create a large document that exceeds the limit
        large_data = "x" * 400000  # 400KB
        request = DocumentSubmissionRequest(
            document_type=DocumentType.INVOICE, document_data=large_data
        )

        with pytest.raises(DocumentValidationError):
            request.validate_size(max_size_bytes=300000)

        # Test with document within limit
        small_data = "x" * 100000  # 100KB
        request = DocumentSubmissionRequest(
            document_type=DocumentType.INVOICE, document_data=small_data
        )
        request.validate_size(max_size_bytes=300000)  # Should not raise


class TestExceptions:
    """Test custom exceptions."""

    def test_myinvois_error(self):
        """Test base MyInvois error."""
        error = MyInvoisError("Test error", "TEST_CODE", {"key": "value"})
        assert str(error) == "Test error"
        assert error.error_code == "TEST_CODE"
        assert error.details == {"key": "value"}

    def test_authentication_error(self):
        """Test authentication error."""
        error = AuthenticationError("Auth failed", {"token_info": "test"})
        assert str(error) == "Auth failed"
        assert error.error_code == "AUTH_ERROR"

    def test_validation_error(self):
        """Test validation error."""
        error = ValidationError("Validation failed", {"field": "error"})
        assert str(error) == "Validation failed"
        assert error.error_code == "VALIDATION_ERROR"
        assert error.details == {"field_errors": {"field": "error"}}

    def test_api_error(self):
        """Test API error."""
        error = APIError("API error", 404, {"message": "Not found"})
        assert str(error) == "API error"
        assert error.error_code == "API_ERROR"
        assert error.status_code == 404

    def test_rate_limit_error(self):
        """Test rate limit error."""
        error = RateLimitError("Rate limit exceeded", 60)
        assert str(error) == "Rate limit exceeded"
        assert error.error_code == "RATE_LIMIT_ERROR"
        assert error.retry_after == 60


class TestConfig:
    """Test configuration."""

    def test_config_creation(self):
        """Test configuration creation."""
        config = MyInvoisConfig(
            api_base_url="https://api.myinvois.hasil.gov.my",
            api_preprod_base_url="https://preprod-api.myinvois.hasil.gov.my",
            client_id="test_client",
            client_secret="test_secret",
            username="test_user",
            password="test_pass",
        )
        assert config.api_base_url == "https://api.myinvois.hasil.gov.my"
        assert config.max_document_size_bytes == 300000

    def test_config_validation(self):
        """Test configuration validation."""
        config = MyInvoisConfig(
            api_base_url="https://api.myinvois.hasil.gov.my",
            api_preprod_base_url="https://preprod-api.myinvois.hasil.gov.my",
            client_id="test_client",
            client_secret="test_secret",
            username="test_user",
            password="test_pass",
        )

        # Should not raise
        config.validate()

        # Test with missing client_id
        config.client_id = ""
        with pytest.raises(ValueError, match="MYINVOIS_CLIENT_ID is required"):
            config.validate()


class TestSecurity:
    """Test security utilities."""

    def test_hash_validator(self):
        """Test hash validation."""
        # Valid SHA-256 hash
        valid_hash = "a" * 64
        assert HashValidator.validate_sha256_hash(valid_hash) is True

        # Invalid hashes
        assert HashValidator.validate_sha256_hash("invalid") is False
        assert HashValidator.validate_sha256_hash("a" * 63) is False  # Too short
        assert HashValidator.validate_sha256_hash("g" * 64) is False  # Invalid hex
        assert HashValidator.validate_sha256_hash("") is False
        assert HashValidator.validate_sha256_hash(None) is False

    def test_hmac_calculation(self):
        """Test HMAC calculation."""
        key = "test_key"
        message = "test_message"

        hmac_result = HashValidator.calculate_hmac(key, message)
        assert hmac_result is not None
        assert len(hmac_result) == 64  # SHA-256 hex length

        # Same input should produce same output
        hmac_result2 = HashValidator.calculate_hmac(key, message)
        assert hmac_result == hmac_result2

    def test_mask_sensitive_string(self):
        """Test sensitive string masking."""
        assert mask_sensitive_string("secret123", visible_chars=4) == "*****t123"
        assert mask_sensitive_string("abc", visible_chars=4) == "***"
        assert mask_sensitive_string("", visible_chars=4) == ""

    def test_security_logger_redaction(self):
        """Test security logger data redaction."""
        logger = SecurityLogger()

        # Test dict redaction
        data = {
            "access_token": "secret_token",
            "username": "test_user",
            "password": "secret_password",
            "normal_field": "normal_value",
        }
        redacted = logger.redact_data(data)
        assert redacted["access_token"] == "[REDACTED]"
        assert redacted["password"] == "[REDACTED]"
        assert redacted["username"] == "test_user"
        assert redacted["normal_field"] == "normal_value"

        # Test string redaction
        sensitive_str = "Bearer secret_token_here"
        redacted_str = logger.redact_data(sensitive_str)
        assert redacted_str == "[REDACTED]"


class TestUtils:
    """Test utility functions."""

    def test_format_datetime(self):
        """Test datetime formatting."""
        dt = datetime(2026, 1, 15, 10, 30, 0)
        formatted = format_datetime(dt)
        assert "2026-01-15T10:30:00" in formatted

    def test_parse_datetime(self):
        """Test datetime parsing."""
        dt_string = "2026-01-15T10:30:00Z"
        parsed = parse_datetime(dt_string)
        assert parsed.year == 2026
        assert parsed.month == 1
        assert parsed.day == 15
        assert parsed.hour == 10
        assert parsed.minute == 30

    def test_validate_document_type(self):
        """Test document type validation."""
        assert validate_document_type("01") == DocumentType.INVOICE
        assert validate_document_type("11") == DocumentType.SELF_BILLED_INVOICE

        with pytest.raises(ValidationError):
            validate_document_type("99")

    def test_validate_document_status(self):
        """Test document status validation."""
        assert validate_document_status("Submitted") == DocumentStatus.SUBMITTED
        assert validate_document_status("Valid") == DocumentStatus.VALID

        with pytest.raises(ValidationError):
            validate_document_status("Unknown")

    def test_validate_uuid(self):
        """Test UUID validation."""
        assert validate_uuid("550e8400-e29b-41d4-a716-446655440000") is True
        assert validate_uuid("invalid-uuid") is False
        assert validate_uuid("") is False
        assert validate_uuid(None) is False

    def test_validate_malaysian_tin(self):
        """Test Malaysian TIN validation."""
        assert is_valid_malaysian_tin("12345678901") is True
        assert is_valid_malaysian_tin("123456789012") is True
        assert is_valid_malaysian_tin("1234567890") is False  # Too short
        assert is_valid_malaysian_tin("1234567890123") is False  # Too long
        assert is_valid_malaysian_tin("12345abc901") is False  # Contains letters
        assert is_valid_malaysian_tin("") is False

    def test_format_currency_malaysia(self):
        """Test Malaysian currency formatting."""
        assert format_currency_malaysia(1234.56) == "RM 1,234.56"
        assert format_currency_malaysia(0) == "RM 0.00"
        assert format_currency_malaysia(1000000) == "RM 1,000,000.00"

    def test_normalize_phone_number_malaysia(self):
        """Test Malaysian phone number normalization."""
        assert normalize_phone_number_malaysia("012-3456789") == "+60123456789"
        assert normalize_phone_number_malaysia("+60 12-3456789") == "+60123456789"
        assert normalize_phone_number_malaysia("60123456789") == "+60123456789"


class TestMyInvoisClient:
    """Test MyInvois client functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return MyInvoisConfig(
            api_base_url="https://api.myinvois.hasil.gov.my",
            api_preprod_base_url="https://preprod-api.myinvois.hasil.gov.my",
            client_id="test_client",
            client_secret="test_secret",
            username="test_user",
            password="test_pass",
        )

    @pytest.fixture
    def client(self, config):
        """Create test client."""
        return MyInvoisClient(config, environment="production")

    def test_client_initialization(self, config):
        """Test client initialization."""
        client = MyInvoisClient(config, environment="production")
        assert client.base_url == "https://api.myinvois.hasil.gov.my"
        assert client.environment == "production"
        client.close()

    def test_client_preprod_initialization(self, config):
        """Test preprod client initialization."""
        client = MyInvoisClient(config, environment="preprod")
        assert client.base_url == "https://preprod-api.myinvois.hasil.gov.my"
        assert client.environment == "preprod"
        client.close()

    @patch("myinvois_client.http_client.MyInvoisHTTPClient.post")
    def test_authenticate(self, mock_post, client):
        """Test authentication."""
        mock_post.return_value = {
            "access_token": "test_access_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        token_info = client.authenticate()
        assert token_info.access_token == "test_access_token"
        assert token_info.token_type == "Bearer"
        assert token_info.expires_in == 3600

    @patch("myinvois_client.http_client.MyInvoisHTTPClient.post")
    def test_submit_document_success(self, mock_post, client):
        """Test successful document submission."""
        # Mock authentication
        with patch.object(client.token_manager, "get_access_token") as mock_auth:
            mock_auth.return_value = TokenInfo(
                access_token="test_token", expires_in=3600, issued_at=datetime.now()
            )

            # Mock submission response
            mock_post.return_value = {
                "uuid": "test-uuid-123",
                "qr_link": "https://myinvois.hasil.gov.my/qr/test-uuid-123",
                "status": "Submitted",
            }

            # Mock duplicate check
            with patch.object(client, "check_duplicate_document") as mock_dup:
                mock_dup.return_value = DuplicateDocumentResponse(is_duplicate=False)

                request = DocumentSubmissionRequest(
                    document_type=DocumentType.INVOICE, document_data={"test": "data"}
                )

                response = client.submit_document(request)
                assert response.document_uuid == "test-uuid-123"
                assert response.status == DocumentStatus.SUBMITTED

    def test_submit_document_size_validation(self, client):
        """Test document size validation on submission."""
        large_data = "x" * 400000
        request = DocumentSubmissionRequest(
            document_type=DocumentType.INVOICE, document_data=large_data
        )

        with pytest.raises(DocumentValidationError):
            client.submit_document(request)

    @patch("myinvois_client.http_client.MyInvoisHTTPClient.get")
    def test_get_document_status(self, mock_get, client):
        """Test document status retrieval."""
        mock_get.return_value = {"status": "Valid", "message": "Document is valid"}

        request = DocumentStatusRequest(document_uuid="test-uuid")
        response = client.get_document_status(request)

        assert response.document_uuid == "test-uuid"
        assert response.status == DocumentStatus.VALID

    def test_get_qr_link(self, client):
        """Test QR link generation."""
        qr_link = client.get_qr_link("test-uuid")
        assert qr_link == "https://myinvois.hasil.gov.my/qr/test-uuid"

    @patch("myinvois_client.http_client.MyInvoisHTTPClient.get")
    def test_check_duplicate_document(self, mock_get, client):
        """Test duplicate document check."""
        mock_get.return_value = {
            "is_duplicate": True,
            "document_uuid": "existing-uuid",
            "message": "Document already exists",
        }

        response = client.check_duplicate_document("test_hash")
        assert response.is_duplicate is True
        assert response.document_uuid == "existing-uuid"


if __name__ == "__main__":
    pytest.main([__file__])
