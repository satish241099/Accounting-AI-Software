# S3 Document Storage Adapter

## Overview

Tenant-scoped S3 document storage adapter for the Malaysia Accounting SaaS platform. Enforces data residency, tenant isolation, and content integrity.

**Module:** `src/kernel/storage/s3_adapter.py`

## Architecture

```
Tenant Context → S3Adapter → AWS S3 (ap-southeast-1)
                 ↓
            SHA-256 Hash → Content-Addressable Keys
                 ↓
            SSE-KMS Encryption
```

## Key Features

### 1. Data Residency (PDPA 2024 Compliance)

- **Region enforcement:** `ap-southeast-1` only
- Rejects any other region at initialization

### 2. Tenant Isolation

- **Key format:** `tenant/{tenant_id}/documents/{sha256_hash}`
- All operations validate tenant scope
- Prevents cross-tenant data leakage

### 3. Content Integrity

- **SHA-256 hashing** for deduplication and tamper detection
- Integrity verification on download
- Detects content modification

### 4. Encryption

- **SSE-KMS required** for all uploads
- KMS key ID must be configured

## Usage

```python
import uuid
from src.kernel.storage.s3_adapter import S3Adapter

adapter = S3Adapter(
    bucket_name="accounting-docs-prod",
    region="ap-southeast-1",
    kms_key_id="arn:aws:kms:ap-southeast-1:123456789012:key/...",
)

tenant_id = uuid.UUID("...")
file_content = b"..."

# Upload
result = adapter.upload_document(
    tenant_id=tenant_id,
    file_content=file_content,
    content_type="image/jpeg",
)

# Download
download = adapter.download_document(tenant_id, result.object_key)

# Pre-signed URL for frontend
url = adapter.get_object_url(result.object_key, expires_in=3600)
```

## Error Types

| Exception | When Raised |
|-----------|-------------|
| `RegionMismatchError` | Region is not `ap-southeast-1` |
| `TenantScopeViolationError` | Object key doesn't match tenant |
| `EncryptionRequiredError` | KMS key not configured for upload |
| `S3AdapterError` | General S3 operation failure |

## Testing

Tests in `test/kernel/storage/test_s3_adapter.py`:
- Tenant-scoped key generation
- SHA-256 content hashing
- Region enforcement
- Tenant scope validation
- SSE-KMS requirement
- Pre-signed URL generation
- Content integrity verification
- Duplicate content handling (same hash → same key)

## AWS Configuration

### Bucket Setup

```bash
aws s3api create-bucket \
  --bucket accounting-docs-prod \
  --region ap-southeast-1 \
  --create-bucket-configuration LocationConstraint=ap-southeast-1
```

### KMS Key

```bash
aws kms create-key \
  --region ap-southeast-1 \
  --description "Accounting SaaS document encryption"
```

### IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
    "Resource": "arn:aws:s3:::accounting-docs-prod/tenant/*"
  }]
}
```

## Integration

Consumed by:
- KB-269 (S3 document storage layer)
- KB-370 (Image processing pipeline)
- KB-348 (OCR pipeline)
- KB-227 (Bank import pipeline)