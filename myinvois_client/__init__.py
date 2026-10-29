"""
MyInvois Intermediary API Client

A production-grade Python client for the LHDN MyInvois e-Invois API,
covering the Login-as-Intermediary System flow that accounting firms use
to submit e-Invoices on behalf of their SME clients.
"""

__version__ = "1.0.0"
__author__ = "Fullstack Forge"
__email__ = "engineering@fullstackforge.com"

from .client import MyInvoisClient
from .exceptions import (
    APIError,
    AuthenticationError,
    MyInvoisError,
    RateLimitError,
    ValidationError,
)
from .models import (
    DocumentStatusResponse,
    DocumentSubmissionRequest,
    DocumentSubmissionResponse,
    LoginResponse,
    TokenInfo,
)

__all__ = [
    "MyInvoisClient",
    "DocumentSubmissionRequest",
    "DocumentSubmissionResponse",
    "DocumentStatusResponse",
    "LoginResponse",
    "TokenInfo",
    "MyInvoisError",
    "AuthenticationError",
    "ValidationError",
    "APIError",
    "RateLimitError",
]
