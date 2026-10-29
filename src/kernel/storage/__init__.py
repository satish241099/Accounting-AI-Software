"""
S3 Document Storage and Image Processing Layer

Provides:
- S3Adapter: Tenant-scoped S3 document storage with ap-southeast-1 residency,
  SSE-KMS encryption, and SHA-256 content-addressable keys
- ImageProcessor: EXIF orientation correction, resize, and optimization utilities
"""

from .s3_adapter import S3Adapter
from .image_processor import ImageProcessor

__all__ = ["S3Adapter", "ImageProcessor"]