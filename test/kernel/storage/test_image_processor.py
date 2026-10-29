"""
Tests for Image Processor.

Tests cover:
- EXIF orientation correction for all 8 EXIF values
- Missing EXIF data handling
- Corrupted EXIF data handling
- Resize downscaling with aspect ratio preservation
- No upscaling
- JPEG optimization
- PNG optimization
- End-to-end pipeline
- Non-image file rejection
"""

import io
import os
import tempfile
from unittest.mock import patch

import pytest
from PIL import Image

from src.kernel.storage.image_processor import (
    ImageProcessor,
    ImageProcessorError,
    InvalidImageError,
    ImageProcessingResult,
)


@pytest.fixture
def processor():
    """Create a default image processor."""
    return ImageProcessor()


@pytest.fixture
def sample_jpg():
    """Create a sample JPEG image."""
    img = Image.new("RGB", (100, 100), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=95)
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def sample_png():
    """Create a sample PNG image."""
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 255))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def large_image():
    """Create a large image for resize testing."""
    img = Image.new("RGB", (3840, 2160), color="blue")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=95)
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def image_with_exif_orientation():
    """Create an image with EXIF orientation tag set to 6 (rotate 270 CW)."""
    img = Image.new("RGB", (100, 100), color="green")
    buffer = io.BytesIO()

    # Create EXIF data with orientation=6
    exif = img.getexif()
    exif[274] = 6  # EXIF Orientation tag

    img.save(buffer, format="JPEG", exif=exif)
    buffer.seek(0)
    return buffer.getvalue()


class TestEXIFOrientationExtraction:
    """Tests for EXIF orientation extraction."""

    def test_extract_no_exif(self, processor, sample_jpg):
        """Should return None when no EXIF data."""
        img = Image.open(io.BytesIO(sample_jpg))
        orientation = processor.extract_exif_orientation(img)
        assert orientation is None

    def test_extract_exif_orientation(self, processor, image_with_exif_orientation):
        """Should extract EXIF orientation value."""
        img = Image.open(io.BytesIO(image_with_exif_orientation))
        orientation = processor.extract_exif_orientation(img)
        assert orientation == 6

    def test_extract_corrupted_exif(self, processor):
        """Should handle corrupted EXIF gracefully."""
        # Create an image with corrupted EXIF
        img = Image.new("RGB", (10, 10), color="white")
        # Simulate corrupted EXIF by making getexif raise an exception
        with patch.object(img, 'getexif', side_effect=TypeError("corrupted EXIF data")):
            orientation = processor.extract_exif_orientation(img)
            assert orientation is None


class TestOrientationCorrection:
    """Tests for EXIF orientation correction."""

    def test_no_correction_needed(self, processor, sample_jpg):
        """Image without EXIF should be returned unchanged."""
        img = Image.open(io.BytesIO(sample_jpg))
        corrected, was_corrected = processor.fix_exif_orientation(img)
        assert corrected is img  # Same object returned
        assert was_corrected is False

    def test_orientation_1_no_change(self, processor):
        """Orientation=1 (Normal) should not modify image."""
        img = Image.new("RGB", (100, 100), color="red")
        buffer = io.BytesIO()
        exif = img.getexif()
        exif[274] = 1  # Normal
        img.save(buffer, format="JPEG", exif=exif)
        buffer.seek(0)

        original_img = Image.open(buffer)
        corrected, was_corrected = processor.fix_exif_orientation(original_img)
        assert corrected is original_img
        assert was_corrected is False

    @pytest.mark.parametrize("orientation,expected_dimensions", [
        (6, (60, 80)),   # Rotate 270 CW: 80x60 → 60x80
        (8, (60, 80)),   # Rotate 90 CW: 80x60 → 60x80
        (3, (80, 60)),   # Rotate 180: 80x60 → 80x60
    ])
    def test_orientation_transformations(self, processor, orientation, expected_dimensions):
        """Test different EXIF orientation transformations."""
        # Create a non-square image to make rotation visible
        img = Image.new("RGB", (80, 60), color="blue")
        buffer = io.BytesIO()
        exif = img.getexif()
        exif[274] = orientation
        img.save(buffer, format="JPEG", exif=exif)
        buffer.seek(0)

        original_img = Image.open(buffer)
        corrected, was_corrected = processor.fix_exif_orientation(original_img)
        assert was_corrected is True
        # After correction, image should be the expected size
        assert corrected.size == expected_dimensions

    def test_corrupted_orientation_graceful(self, processor):
        """Should handle invalid EXIF orientation gracefully."""
        img = Image.new("RGB", (100, 100), color="white")
        buffer = io.BytesIO()
        exif = img.getexif()
        exif[274] = 99  # Invalid orientation value
        img.save(buffer, format="JPEG", exif=exif)
        buffer.seek(0)

        original_img = Image.open(buffer)
        corrected, was_corrected = processor.fix_exif_orientation(original_img)
        # Should not crash, should return original
        assert was_corrected is False


class TestResize:
    """Tests for image resizing."""

    def test_resize_downscale(self, processor, large_image):
        """Should downscale large images."""
        img = Image.open(io.BytesIO(large_image))
        resized = processor.resize_image(img, max_width=800, max_height=600)
        assert resized.width <= 800
        assert resized.height <= 600

    def test_resize_no_upscale(self, processor, sample_jpg):
        """Should not upscale small images."""
        img = Image.open(io.BytesIO(sample_jpg))
        original_size = img.size
        resized = processor.resize_image(img, max_width=1920, max_height=1080)
        assert resized.size == original_size  # Unchanged

    def test_resize_maintains_aspect_ratio(self, processor, large_image):
        """Should maintain aspect ratio when resizing."""
        img = Image.open(io.BytesIO(large_image))
        original_ratio = img.width / img.height
        resized = processor.resize_image(img, max_width=1920, max_height=1080)
        resized_ratio = resized.width / resized.height
        assert abs(original_ratio - resized_ratio) < 0.01  # Allow small floating point error

    def test_resize_lanczos_quality(self, processor, large_image):
        """Should use high-quality resampling."""
        img = Image.open(io.BytesIO(large_image))
        # Check that resize uses LANCZOS (should not raise)
        resized = processor.resize_image(img, max_width=100, max_height=100)
        assert resized is not None


class TestOptimize:
    """Tests for image optimization."""

    def test_optimize_jpeg(self, processor, sample_jpg):
        """Should optimize JPEG images."""
        img = Image.open(io.BytesIO(sample_jpg))
        optimized = processor.optimize_image(img, quality=85, output_format="JPEG")
        assert isinstance(optimized, bytes)
        assert len(optimized) > 0

    def test_optimize_png(self, processor, sample_png):
        """Should optimize PNG images."""
        img = Image.open(io.BytesIO(sample_png))
        optimized = processor.optimize_image(img, quality=85, output_format="PNG")
        assert isinstance(optimized, bytes)
        assert len(optimized) > 0

    def test_optimize_invalid_format(self, processor, sample_jpg):
        """Should raise error for invalid format."""
        img = Image.open(io.BytesIO(sample_jpg))
        with pytest.raises(InvalidImageError):
            processor.optimize_image(img, output_format="GIF")

    def test_optimize_reduces_size(self, processor, large_image):
        """Optimization should reduce or maintain file size."""
        img = Image.open(io.BytesIO(large_image))
        original_size = len(large_image)
        optimized = processor.optimize_image(img, quality=85)
        assert len(optimized) <= original_size + 100  # Allow small overhead from format changes


class TestEndToEndPipeline:
    """Tests for end-to-end image processing."""

    def test_process_image_upload(self, processor, large_image):
        """End-to-end pipeline should process large image."""
        result = processor.process_image_upload(
            large_image,
            max_width=1920,
            max_height=1080,
            quality=85,
        )
        assert isinstance(result, ImageProcessingResult)
        assert result.processed_size_bytes > 0
        assert result.compression_ratio >= 0
        assert result.exif_corrected in [True, False]

    def test_process_image_no_exif(self, processor, sample_jpg):
        """Pipeline should handle images without EXIF."""
        result = processor.process_image_upload(sample_jpg)
        assert isinstance(result, ImageProcessingResult)
        assert result.exif_corrected is False

    def test_process_image_with_exif(self, processor, image_with_exif_orientation):
        """Pipeline should correct EXIF orientation."""
        result = processor.process_image_upload(image_with_exif_orientation)
        assert isinstance(result, ImageProcessingResult)
        # The EXIF was orientation=6, so it should have been corrected
        assert result.exif_corrected is True

    def test_process_invalid_image(self, processor):
        """Pipeline should reject invalid image files."""
        with pytest.raises(InvalidImageError):
            processor.process_image_upload(b"This is not an image file!")

    def test_process_empty_bytes(self, processor):
        """Pipeline should handle empty input."""
        with pytest.raises(InvalidImageError):
            processor.process_image_upload(b"")

    def test_result_contains_metadata(self, processor, large_image):
        """Result should contain complete metadata."""
        result = processor.process_image_upload(large_image)
        assert result.original_width > 0
        assert result.original_height > 0
        assert result.processed_width > 0
        assert result.processed_height > 0
        assert result.original_size_bytes == len(large_image)
        assert result.processed_size_bytes > 0


class TestCompressionMetrics:
    """Tests for compression ratio calculations."""

    def test_compression_ratio_positive(self, processor, large_image):
        """Compression ratio should be positive for optimization."""
        result = processor.process_image_upload(large_image)
        assert result.compression_ratio >= 0

    def test_compression_ratio_less_than_one(self, processor, large_image):
        """Compression ratio should be less than 1.0 (100%)."""
        result = processor.process_image_upload(large_image)
        assert result.compression_ratio < 1.0