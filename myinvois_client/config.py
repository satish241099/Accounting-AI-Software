"""
Configuration management for the MyInvois Intermediary API Client.
"""

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from dotenv import load_dotenv

if TYPE_CHECKING:
    from botocore.client import BaseClient

# Load environment variables from .env file
load_dotenv()


@dataclass
class MyInvoisConfig:
    """Configuration for MyInvois API client."""

    # API Configuration
    api_base_url: str
    api_preprod_base_url: str

    # Authentication
    client_id: str
    client_secret: str
    username: str
    password: str

    # Security
    max_document_size_bytes: int = 300000
    token_buffer_seconds: int = 60
    max_retries: int = 3
    retry_delay_seconds: int = 1

    # Rate limiting
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst_size: int = 10

    # AWS Configuration (for secrets)
    aws_region: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_session_token: str | None = None

    # Certificate Configuration
    certificate_path: str | None = None
    certificate_password: str | None = None

    # Logging
    log_level: str = "INFO"
    structured_logging: bool = True

    # Tenant context
    default_tenant_id: str | None = None

    @classmethod
    def from_environment(cls) -> "MyInvoisConfig":
        """Create configuration from environment variables."""
        return cls(
            # API Configuration
            api_base_url=os.getenv("MYINVOIS_API_BASE_URL", "https://api.myinvois.hasil.gov.my"),
            api_preprod_base_url=os.getenv(
                "MYINVOIS_API_PREPROD_BASE_URL", "https://preprod-api.myinvois.hasil.gov.my"
            ),
            # Authentication
            client_id=os.getenv("MYINVOIS_CLIENT_ID", ""),
            client_secret=os.getenv("MYINVOIS_CLIENT_SECRET", ""),
            username=os.getenv("MYINVOIS_USERNAME", ""),
            password=os.getenv("MYINVOIS_PASSWORD", ""),
            # Security
            max_document_size_bytes=int(os.getenv("MYINVOIS_MAX_DOCUMENT_SIZE", "300000")),
            token_buffer_seconds=int(os.getenv("MYINVOIS_TOKEN_BUFFER_SECONDS", "60")),
            max_retries=int(os.getenv("MYINVOIS_MAX_RETRIES", "3")),
            retry_delay_seconds=int(os.getenv("MYINVOIS_RETRY_DELAY_SECONDS", "1")),
            # Rate limiting
            rate_limit_requests_per_minute=int(os.getenv("MYINVOIS_RATE_LIMIT_RPM", "60")),
            rate_limit_burst_size=int(os.getenv("MYINVOIS_RATE_LIMIT_BURST", "10")),
            # AWS Configuration
            aws_region=os.getenv("AWS_REGION"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
            # Certificate Configuration
            certificate_path=os.getenv("MYINVOIS_CERTIFICATE_PATH"),
            certificate_password=os.getenv("MYINVOIS_CERTIFICATE_PASSWORD"),
            # Logging
            log_level=os.getenv("MYINVOIS_LOG_LEVEL", "INFO"),
            structured_logging=os.getenv("MYINVOIS_STRUCTURED_LOGGING", "true").lower() == "true",
            # Tenant context
            default_tenant_id=os.getenv("MYINVOIS_DEFAULT_TENANT_ID"),
        )

    def validate(self) -> None:
        """Validate configuration values."""
        if not self.client_id:
            raise ValueError("MYINVOIS_CLIENT_ID is required")
        if not self.client_secret:
            raise ValueError("MYINVOIS_CLIENT_SECRET is required")
        if not self.username:
            raise ValueError("MYINVOIS_USERNAME is required")
        if not self.password:
            raise ValueError("MYINVOIS_PASSWORD is required")

        if self.max_document_size_bytes <= 0:
            raise ValueError("MYINVOIS_MAX_DOCUMENT_SIZE must be positive")
        if self.token_buffer_seconds < 0:
            raise ValueError("MYINVOIS_TOKEN_BUFFER_SECONDS must be non-negative")
        if self.max_retries < 0:
            raise ValueError("MYINVOIS_MAX_RETRIES must be non-negative")
        if self.retry_delay_seconds < 0:
            raise ValueError("MYINVOIS_RETRY_DELAY_SECONDS must be non-negative")

        if self.rate_limit_requests_per_minute <= 0:
            raise ValueError("MYINVOIS_RATE_LIMIT_RPM must be positive")
        if self.rate_limit_burst_size <= 0:
            raise ValueError("MYINVOIS_RATE_LIMIT_BURST must be positive")

        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            raise ValueError(f"MYINVOIS_LOG_LEVEL must be one of {valid_log_levels}")


class SecretProvider:
    """Base class for secret providers."""

    def get_client_secret(self) -> str:
        """Get client secret."""
        raise NotImplementedError

    def get_certificate(self) -> str:
        """Get certificate content."""
        raise NotImplementedError


class EnvironmentSecretProvider(SecretProvider):
    """Secret provider from environment variables (for development only)."""

    def __init__(self, config: MyInvoisConfig):
        self.config = config

    def get_client_secret(self) -> str:
        """Get client secret from environment."""
        secret = self.config.client_secret
        if not secret:
            raise ValueError("Client secret not available in environment")
        return secret

    def get_certificate(self) -> str:
        """Get certificate from environment or file."""
        if self.config.certificate_path:
            with open(self.config.certificate_path) as f:
                return f.read()
        elif os.getenv("MYINVOIS_CERTIFICATE_CONTENT"):
            return os.getenv("MYINVOIS_CERTIFICATE_CONTENT", "")
        else:
            raise ValueError("Certificate not available in environment or file")


class AWSSecretProvider(SecretProvider):
    """Secret provider from AWS Secrets Manager."""

    def __init__(self, config: MyInvoisConfig) -> None:
        self.config = config
        self._client: "BaseClient | None" = None

    @property
    def client(self) -> "BaseClient":
        """Lazy-load AWS Secrets Manager client."""
        if self._client is None:
            import boto3  # noqa: PLC0414

            self._client = boto3.client(  # type: ignore[call-arg]
                "secretsmanager",
                region_name=self.config.aws_region,
                aws_access_key_id=self.config.aws_access_key_id,
                aws_secret_access_key=self.config.aws_secret_access_key,
                aws_session_token=self.config.aws_session_token,
            )
        return self._client

    def get_client_secret(self) -> str:
        """Get client secret from AWS Secrets Manager."""
        secret_name = os.getenv("MYINVOIS_CLIENT_SECRET_NAME", "myinvois/client-secret")
        try:
            response = self.client.get_secret_value(SecretId=secret_name)  # type: ignore[union-attr]
            return str(response["SecretString"])  # type: ignore[index]
        except Exception as e:
            raise ValueError(f"Failed to retrieve client secret from AWS: {e}") from e

    def get_certificate(self) -> str:
        """Get certificate from AWS Secrets Manager."""
        secret_name = os.getenv("MYINVOIS_CERTIFICATE_NAME", "myinvois/certificate")
        try:
            response = self.client.get_secret_value(SecretId=secret_name)  # type: ignore[union-attr]
            return str(response["SecretString"])  # type: ignore[index]
        except Exception as e:
            raise ValueError(f"Failed to retrieve certificate from AWS: {e}") from e
