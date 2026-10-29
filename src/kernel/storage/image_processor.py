"""
Image processing utilities for document uploads.

Provides:
- EXIF orientation correction (fixes sideways/upside-down phone photos)
- Image resize with aspect ratio preservation
- Image optimization for storage and performance
"""

import io
from dataclasses import dataclass
from typing import Optional, Tuple, Union

from PIL import Image, ExifTags


@dataclass(frozen=True)
class ImageProcessingResult:
    """Result of image processing pipeline."""

    processed_bytes: bytes
    original_width: int
    original_height: int
    processed_width: int
    processed_height: int
    original_size_bytes: int
    processed_size_bytes: int
    compression_ratio: float
    exif_corrected: bool


class ImageProcessorError(Exception):
    """Base exception for image processor errors."""

    pass


class InvalidImageError(ImageProcessorError):
    """Raised when input is not a valid image."""

    pass


class ImageProcessor:
    """
    Image processing utilities for document uploads.

    Handles EXIF orientation correction, resize, and optimization for
    mobile-captured receipts and invoices.
    """

    # EXIF Orientation tag constants
    EXIF_ORIENTATION_TAG = 274  # Orientation tag in EXIF data

    # EXIF orientation value mappings
    # See: https://exiftool.org/TagNames/EXIF.html
    EXIF_ORIENTATION_TRANSFORMS = {
        1: "Normal",  # No transformation needed
        2: "Flip horizontal",
        3: "Rotate 180",
        4: "Flip vertical",
        5: "Transpose",
        6: "Rotate 270",  # Rotate 90 CW
        7: "Transverse",
        8: "Rotate 90",  # Rotate 270 CW (or 90 CCW)
    }

    def __init__(self, default_quality: int = 85, default_format: str = "JPEG"):
        """
        Initialize the image processor.

        Args:
            default_quality: JPEG quality (1-100, default: 85).
            default_format: Output format (default: 'JPEG').
        """
        self._default_quality = default_quality
        self._default_format = default_format

    @staticmethod
    def extract_exif_orientation(image: Image.Image) -> Optional[int]:
        """
        Extract EXIF Orientation value from an image.

        Args:
            image: PIL Image object.

        Returns:
            EXIF orientation value (1-8) if present, None otherwise.
        """
        try:
            exif_data = image.getexif()
            if exif_data is None:
                return None

            # EXIF Orientation tag is 274
            orientation = exif_data.get(274)
            return orientation
        except (AttributeError, KeyError, TypeError):
            # Image has no EXIF data or EXIF is corrupted
            return None

    @staticmethod
    def apply_orientation_transformation(
        image: Image.Image, orientation: int
    ) -> Image.Image:
        """
        Apply EXIF orientation transformation to an image.

        Args:
            image: PIL Image object.
            orientation: EXIF orientation value (1-8).

        Returns:
            Transformed PIL Image object.

        Raises:
            ValueError: If orientation value is not 1-8.
        """
        if not 1 <= orientation <= 8:
            raise ValueError(f"Invalid EXIF orientation value: {orientation}. Must be 1-8.")

        if orientation == 1:
            # Normal - no transformation needed
            return image

        transformations = {
            2: lambda img: img.transpose(Image.Transpose.FLIP_LEFT_RIGHT),
            3: lambda img: img.rotate(180, expand=True),
            4: lambda img: img.transpose(Image.Transpose.FLIP_TOP_BOTTOM),
            5: lambda img: img.transpose(Image.Transpose.TRANSPOSE),
            6: lambda img: img.rotate(270, expand=True),
            7: lambda img: img.transpose(Image.Transpose.TRANSVERSE),
            8: lambda img: img.rotate(90, expand=True),
        }

        transform = transformations.get(orientation)
        if transform:
            return transform(image)

        return image

    def fix_exif_orientation(self, image: Image.Image) -> Tuple[Image.Image, bool]:
        """
        Fix EXIF orientation on an image.

        Args:
            image: PIL Image object.

        Returns:
            Tuple of (corrected_image, was_corrected).
            If no EXIF orientation or orientation=1, returns original image.
        """
        orientation = self.extract_exif_orientation(image)

        if orientation is None or orientation == 1:
            # No orientation correction needed
            return image, False

        try:
            corrected = self.apply_orientation_transformation(image, orientation)
            # Remove EXIF orientation tag after correction to prevent double-rotation
            self._clear_exif_orientation(corrected)
            return corrected, True
        except (ValueError, Exception):
            # If transformation fails, return original image unchanged
            return image, False

    @staticmethod
    def _clear_exif_orientation(image: Image.Image) -> None:
        """Clear EXIF orientation tag after correction."""
        try:
            exif = image.getexif()
            if exif is not None:
                exif[Image.ExifTags.Base.orientation] = 1  # Set to normal
        except (AttributeError, KeyError):
            pass

    def resize_image(
        self,
        image: Image.Image,
        max_width: int = 1920,
        max_height: int = 1080,
        maintain_aspect: bool = True,
    ) -> Image.Image:
        """
        Resize an image, only downscaling (never upscaling).

        Args:
            image: PIL Image object.
            max_width: Maximum width in pixels (default: 1920).
            max_height: Maximum height in pixels (default: 1080).
            maintain_aspect: Whether to maintain aspect ratio (default: True).

        Returns:
            Resized PIL Image object. If image is already smaller than max dimensions,
            returns the original image unchanged.
        """
        original_width, original_height = image.size

        # Only downscale, never upscale
        if original_width <= max_width and original_height <= max_height:
            return image

        if maintain_aspect:
            # Calculate new dimensions maintaining aspect ratio
            width_ratio = max_width / original_width
            height_ratio = max_height / original_height
            ratio = min(width_ratio, height_ratio)

            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
        else:
            new_width = max_width
            new_height = max_height

        # Use LANCZOS resampling for high-quality downscaling
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def optimize_image(
        self,
        image: Image.Image,
        quality: Optional[int] = None,
        output_format: Optional[str] = None,
        strip_metadata: bool = True,
    ) -> bytes:
        """
        Optimize an image for storage and web delivery.

        Args:
            image: PIL Image object.
            quality: JPEG quality (1-100). Defaults to instance default.
            output_format: Output format ('JPEG' or 'PNG'). Defaults to instance default.
            strip_metadata: Whether to strip EXIF/metadata (default: True).

        Returns:
            Optimized image bytes.

        Raises:
            InvalidImageError: If image cannot be saved in the specified format.
        """
        quality = quality if quality is not None else self._default_quality
        output_format = output_format if output_format is not None else self._default_format
        output_format = output_format.upper()

        buffer = io.BytesIO()

        save_kwargs = {}

        if output_format == "JPEG":
            save_kwargs = {
                "format": "JPEG",
                "quality": quality,
                "optimize": True,
                "progressive": True,
            }
            # When strip_metadata is True, we want to ensure EXIF is not included
            # in the saved image. We do this by NOT passing the exif key at all;
            # PIL will then use the image's current EXIF data (which should be
            # minimal after fix_exif_orientation clears the orientation tag).
            # Passing exif=None causes PIL to crash with: TypeError: object of
            # type 'NoneType' has no len()
            if strip_metadata:
                # Remove exif from save_kwargs entirely to let PIL handle it
                # based on the image's current state
                save_kwargs.pop("exif", None)
                # Explicitly set exif to empty bytes to clear it in all PIL versions
                save_kwargs["exif"] = b""
        elif output_format == "PNG":
            save_kwargs = {
                "format": "PNG",
                "optimize": True,
            }
            if strip_metadata:
                # PNG doesn't have EXIF in the same way, but we can strip all metadata
                pass
        else:
            raise InvalidImageError(f"Unsupported output format: {output_format}. Use JPEG or PNG.")

        try:
            # Convert to RGB if necessary (for JPEG, which doesn't support alpha)
            if output_format == "JPEG" and image.mode in ("RGBA", "LA", "P"):
                # Create white background for transparent images
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                if image.mode in ("RGBA", "LA"):
                    background.paste(image, mask=image.split()[-1])
                    image = background
                else:
                    image = image.convert("RGB")
            elif output_format == "JPEG" and image.mode != "RGB":
                image = image.convert("RGB")

            image.save(buffer, **save_kwargs)
            return buffer.getvalue()
        except (IOError, OSError) as e:
            raise InvalidImageError(f"Failed to optimize image: {e}")

    def process_image_upload(
        self,
        file_bytes: bytes,
        max_width: int = 1920,
        max_height: int = 1080,
        quality: int = 85,
        output_format: str = "JPEG",
    ) -> ImageProcessingResult:
        """
        End-to-end image processing pipeline for uploads.

        Pipeline:
        1. Load image
        2. Fix EXIF orientation
        3. Resize to max dimensions
        4. Optimize for storage

        Args:
            file_bytes: Raw image file bytes.
            max_width: Maximum width after resize.
            max_height: Maximum height after resize.
            quality: JPEG quality (1-100).
            output_format: Output format ('JPEG' or 'PNG').

        Returns:
            ImageProcessingResult with processed bytes and metadata.

        Raises:
            InvalidImageError: If input is not a valid image.
        """
        original_size = len(file_bytes)

        try:
            # Load image
            image = Image.open(io.BytesIO(file_bytes))
            image.load()  # Force load to catch corrupted images early

            original_width, original_height = image.size
            original_mode = image.mode

            # Step 1: Fix EXIF orientation
            image, exif_corrected = self.fix_exif_orientation(image)

            # Step 2: Resize
            image = self.resize_image(image, max_width, max_height, maintain_aspect=True)

            # Step 3: Optimize
            processed_bytes = self.optimize_image(
                image, quality=quality, output_format=output_format, strip_metadata=True
            )

            processed_size = len(processed_bytes)
            compression_ratio = (original_size - processed_size) / original_size if original_size > 0 else 0.0

            # Get final dimensions (may have changed during optimization if format conversion)
            processed_image = Image.open(io.BytesIO(processed_bytes))
            processed_width, processed_height = processed_image.size

            return ImageProcessingResult(
                processed_bytes=processed_bytes,
                original_width=original_width,
                original_height=original_height,
                processed_width=processed_width,
                processed_height=processed_height,
                original_size_bytes=original_size,
                processed_size_bytes=processed_size,
                compression_ratio=compression_ratio,
                exif_corrected=exif_corrected,
            )

        except (IOError, OSError, Image.UnidentifiedImageError) as e:
            raise InvalidImageError(f"Invalid image file: {e}")