# MyInvois Intermediary API Client

A production-grade Python client for the LHDN MyInvois e-Invois API, covering the Login-as-Intermediary System flow that accounting firms use to submit e-Invoices on behalf of their SME clients.

## Features

- **Authentication**: Login as Intermediary System with automatic token refresh (60-minute token lifetime)
- **Document Submission**: Submit e-Invoices with SHA-256 documentHash validation
- **Size Validation**: Enforces 300KB submission limit before network calls
- **Document Types**: Supports all MyInvois document types (01-04, 11-14)
- **Status Polling**: Full status lifecycle handling (Submitted/Valid/Invalid/Cancelled)
- **Duplicate Detection**: Explicit duplicate document handling per MyInvois rules
- **QR Link Generation**: Automatic QR link generation from document UUID
- **Certificate Validation**: v1.1 signature validation with CA-issued digital certificates
- **Type Safety**: Fully type-annotated with mypy strict mode compliance
- **Security**: Structured logging, credential redaction, secure secret management
- **AWS Integration**: Native AWS Secrets Manager/SSM Parameter Store support
- **Rate Limiting**: Configurable rate limiting with exponential backoff retry logic
- **Tenant Context**: Per-client audit trails for every API call

## Requirements

- Python 3.12+
- MyInvois Intermediary System credentials
- AWS account (for production secret management)

## Installation

```bash
pip install myinvois-client
```

For development:

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from myinvois_client import MyInvoisClient, DocumentType, DocumentSubmissionRequest

# Configure the client
config = MyInvoisConfig(
    api_base_url="https://api.myinvois.hasil.gov.my",
    api_preprod_base_url="https://preprod-api.myinvois.hasil.gov.my",
    client_id="your_client_id",
    client_secret="your_client_secret",
    username="your_username",
    password="your_password"
)

# Create client (uses environment variables by default)
client = MyInvoisClient(config, environment="production")

# Authenticate
token = client.authenticate()

# Submit an invoice
request = DocumentSubmissionRequest(
    document_type=DocumentType.INVOICE,
    document_data={
        "supplierTin": "C1234567890",
        "customerTin": "C0987654321",
        "invoiceNumber": "INV-2024-001",
        "invoiceDate": "2024-01-15",
        "currencyCode": "MYR",
        "lineItems": [...]
    },
    tenant_id="client-123"
)

response = client.submit_document(request)
print(f"Submitted: {response.document_uuid}")
print(f"QR Link: {response.qr_link}")

# Check status
status = client.get_document_status(
    DocumentStatusRequest(document_uuid=response.document_uuid)
)
print(f"Status: {status.status}")

client.close()
```

## Configuration

The client can be configured via environment variables or programmatically:

### Environment Variables

```bash
# Required
MYINVOIS_CLIENT_ID=your_client_id
MYINVOIS_CLIENT_SECRET=your_client_secret
MYINVOIS_USERNAME=your_username
MYINVOIS_PASSWORD=your_password

# Optional
MYINVOIS_API_BASE_URL=https://api.myinvois.hasil.gov.my
MYINVOIS_API_PREPROD_BASE_URL=https://preprod-api.myinvois.hasil.gov.my
MYINVOIS_MAX_DOCUMENT_SIZE=300000
MYINVOIS_TOKEN_BUFFER_SECONDS=60
MYINVOIS_MAX_RETRIES=3
MYINVOIS_RETRY_DELAY_SECONDS=1
MYINVOIS_RATE_LIMIT_RPM=60
MYINVOIS_RATE_LIMIT_BURST=10
MYINVOIS_LOG_LEVEL=INFO
MYINVOIS_STRUCTURED_LOGGING=true
MYINVOIS_DEFAULT_TENANT_ID=default_tenant

# AWS (for production)
AWS_REGION=ap-southeast-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
MYINVOIS_CLIENT_SECRET_NAME=myinvois/client-secret
MYINVOIS_CERTIFICATE_NAME=myinvois/certificate
```

### Programmatic Configuration

```python
from myinvois_client import MyInvoisConfig

config = MyInvoisConfig(
    api_base_url="https://api.myinvois.hasil.gov.my",
    api_preprod_base_url="https://preprod-api.myinvois.hasil.gov.my",
    client_id="your_client_id",
    client_secret="your_client_secret",
    username="your_username",
    password="your_password",
    max_document_size_bytes=300000,
    token_buffer_seconds=60,
    max_retries=3,
    retry_delay_seconds=1,
    rate_limit_requests_per_minute=60,
    rate_limit_burst_size=10,
    log_level="INFO",
    structured_logging=True,
)
```

## Document Types

| Code | Description |
|------|-------------|
| 01 | Invoice |
| 02 | Credit Note |
| 03 | Debit Note |
| 04 | Receipt |
| 11 | Self-Billed Invoice |
| 12 | Self-Billed Credit Note |
| 13 | Self-Billed Debit Note |
| 14 | Self-Billed Receipt |

## Document Status

| Status | Description |
|--------|-------------|
| Submitted | Document submitted to MyInvois |
| Valid | Document validated successfully |
| Invalid | Document failed validation |
| Cancelled | Document cancelled |

## Security

The client implements several security measures:

- **Credential Redaction**: Automatic redaction of sensitive data from logs
- **No Plaintext Secrets**: Credentials never logged, never persisted in plaintext
- **AWS Secrets Manager**: Production-grade secret management
- **Certificate Validation**: v1.1 CA certificate validation
- **Structured Logging**: JSON-formatted logs with security context
- **Token Protection**: Access tokens never included in error messages or traces

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=myinvois_client --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
```

## Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Type check
mypy myinvois_client

# Run all quality checks
ruff check . && black --check . && mypy myinvois_client
```

## Project Structure

```
myinvois_client/
├── __init__.py          # Package exports
├── client.py            # Main client implementation
├── config.py            # Configuration management
├── models.py            # Data models and types
├── exceptions.py        # Custom exceptions
├── http_client.py       # HTTP client with retry logic
├── security.py          # Security utilities
└── utils.py             # Helper functions

tests/
├── __init__.py
└── test_client.py       # Comprehensive test suite
```

## API Reference

### MyInvoisClient

#### `__init__(config, secret_provider=None, environment="production")`
Initialize the client.

#### `authenticate() -> TokenInfo`
Authenticate with MyInvois API.

#### `submit_document(request) -> DocumentSubmissionResponse`
Submit a document.

#### `check_duplicate_document(document_hash, tenant_id=None) -> DuplicateDocumentResponse`
Check for duplicate documents.

#### `get_document_status(request) -> DocumentStatusResponse`
Get document status.

#### `wait_for_document_status(document_uuid, target_status, max_wait_seconds=300, poll_interval_seconds=5, tenant_id=None) -> DocumentStatusResponse`
Wait for document to reach target status.

#### `get_qr_link(document_uuid) -> str`
Get QR link for document.

#### `close()`
Close client and cleanup resources.

### Configuration

See `MyInvoisConfig` class for all configuration options.

## Compliance

This client implements the MyInvois Intermediary API specification as verified on 21 Oct 2026:

- ✅ Login as Intermediary System API
- ✅ 60-minute token lifetime with automatic refresh
- ✅ SHA-256 documentHash computation
- ✅ 300KB submission limit enforcement
- ✅ Document types 01, 02, 03, 04, 11, 12, 13, 14
- ✅ Full status lifecycle (Submitted/Valid/Invalid/Cancelled)
- ✅ Duplicate detection per published rules
- ✅ QR link format compliance
- ✅ v1.1 CA certificate signature validation

## License

MIT License - see LICENSE file for details.

## Support

For issues and feature requests, please contact the Fullstack Forge engineering team.