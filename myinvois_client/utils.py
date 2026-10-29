"""
Utility functions for the MyInvois API client.
"""

import json
import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode

from .exceptions import ValidationError
from .models import DocumentStatus, DocumentType


def format_datetime(dt: datetime) -> str:
    """
    Format datetime in ISO 8601 format required by MyInvois API.

    Args:
        dt: Datetime to format

    Returns:
        ISO 8601 formatted string
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.isoformat()


def parse_datetime(dt_string: str) -> datetime:
    """
    Parse datetime string from MyInvois API response.

    Args:
        dt_string: ISO 8601 datetime string

    Returns:
        Parsed datetime object

    Raises:
        ValidationError: If datetime string is invalid
    """
    try:
        return datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as e:
        raise ValidationError(f"Invalid datetime format: {dt_string}", {"datetime": str(e)}) from e


def validate_document_type(document_type: str) -> DocumentType:
    """
    Validate and convert document type string to DocumentType enum.

    Args:
        document_type: Document type string

    Returns:
        DocumentType enum

    Raises:
        ValidationError: If document type is invalid
    """
    try:
        return DocumentType(document_type)
    except ValueError as e:
        valid_types = [dt.value for dt in DocumentType]
        raise ValidationError(
            f"Invalid document type: {document_type}. Valid types: {valid_types}",
            {"document_type": document_type},
        ) from e


def validate_document_status(status: str) -> DocumentStatus:
    """
    Validate and convert status string to DocumentStatus enum.

    Args:
        status: Status string

    Returns:
        DocumentStatus enum

    Raises:
        ValidationError: If status is invalid
    """
    try:
        return DocumentStatus(status)
    except ValueError as e:
        valid_statuses = [ds.value for ds in DocumentStatus]
        raise ValidationError(
            f"Invalid document status: {status}. Valid statuses: {valid_statuses}",
            {"status": status},
        ) from e


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file operations.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove or replace dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(" .")
    # Limit length
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    return sanitized


def build_query_string(params: dict[str, Any]) -> str:
    """
    Build URL query string from parameters.

    Args:
        params: Query parameters

    Returns:
        URL-encoded query string
    """
    filtered_params = {k: v for k, v in params.items() if v is not None}
    return urlencode(filtered_params)


def safe_json_dumps(data: Any, **kwargs: Any) -> str:
    """
    Safely serialize data to JSON with error handling.

    Args:
        data: Data to serialize
        **kwargs: Additional json.dumps arguments

    Returns:
        JSON string

    Raises:
        ValidationError: If serialization fails
    """
    try:
        return json.dumps(data, **kwargs)
    except (TypeError, ValueError) as e:
        raise ValidationError(f"JSON serialization failed: {e}", {"error": str(e)}) from e


def safe_json_loads(json_string: str) -> Any:
    """
    Safely deserialize JSON string with error handling.

    Args:
        json_string: JSON string to deserialize

    Returns:
        Deserialized data

    Raises:
        ValidationError: If deserialization fails
    """
    try:
        return json.loads(json_string)
    except (TypeError, ValueError) as e:
        raise ValidationError(f"JSON deserialization failed: {e}", {"error": str(e)}) from e


def generate_correlation_id() -> str:
    """
    Generate a unique correlation ID for request tracking.

    Returns:
        Unique correlation ID string
    """
    import uuid

    return str(uuid.uuid4())


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.1f} GB"


def chunk_list(data: list[Any], chunk_size: int) -> list[list[Any]]:
    """
    Split a list into chunks of specified size.

    Args:
        data: List to split
        chunk_size: Size of each chunk

    Returns:
        List of chunks

    Raises:
        ValidationError: If chunk size is invalid
    """
    if chunk_size <= 0:
        raise ValidationError("Chunk size must be positive", {"chunk_size": str(chunk_size)})

    return [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]


def mask_sensitive_string(sensitive_string: str, visible_chars: int = 4) -> str:
    """
    Mask a sensitive string for logging purposes.

    Args:
        sensitive_string: String to mask
        visible_chars: Number of characters to keep visible at the end

    Returns:
        Masked string
    """
    if not sensitive_string:
        return ""

    if len(sensitive_string) <= visible_chars:
        return "*" * len(sensitive_string)

    return "*" * (len(sensitive_string) - visible_chars) + sensitive_string[-visible_chars:]


def validate_uuid(uuid_string: str) -> bool:
    """
    Validate UUID string format.

    Args:
        uuid_string: UUID string to validate

    Returns:
        True if valid UUID
    """
    import uuid

    try:
        uuid.UUID(uuid_string)
        return True
    except (ValueError, TypeError, AttributeError):
        return False


def extract_error_message(response_data: dict[str, Any]) -> str:
    """
    Extract error message from API response data.

    Args:
        response_data: API response data

    Returns:
        Error message string
    """
    # Common error message fields
    message_fields = ["message", "error", "error_message", "detail", "description"]

    for field in message_fields:
        if field in response_data and response_data[field]:
            return str(response_data[field])

    # If no standard message field, return a generic message
    return "An error occurred while processing the request"


def is_valid_malaysian_tin(tin: str) -> bool:
    """
    Validate Malaysian Tax Identification Number (TIN) format.

    Args:
        tin: TIN string to validate

    Returns:
        True if valid TIN format
    """
    if not isinstance(tin, str):
        return False

    # Remove spaces and dashes
    cleaned_tin = re.sub(r"[\s-]", "", tin)

    # Malaysian TIN is typically 11-12 digits
    if not cleaned_tin.isdigit():
        return False

    return len(cleaned_tin) in [11, 12]


def format_currency_malaysia(amount: int | float) -> str:
    """
    Format currency amount in Malaysian format (RM).

    Args:
        amount: Amount to format

    Returns:
        Formatted currency string
    """
    return f"RM {amount:,.2f}"


def normalize_phone_number_malaysia(phone: str) -> str:
    """
    Normalize Malaysian phone number format.

    Args:
        phone: Phone number string

    Returns:
        Normalized phone number
    """
    # Remove all non-digit characters
    digits = re.sub(r"\D", "", phone)

    # Handle country code
    if digits.startswith("60"):
        digits = digits[2:]
    elif digits.startswith("0"):
        digits = digits[1:]

    # Add country code back
    return f"+60{digits}"
