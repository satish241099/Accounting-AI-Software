# Image Processing Pipeline

## Overview

The image processing pipeline handles mobile-captured receipts, invoices, and tax documents. It corrects EXIF orientation, resizes to standard dimensions, and optimizes file sizes for storage efficiency.

**Module:** `src/kernel/storage/image_processor.py`

## Architecture

```
Upload → Load → Fix EXIF → Resize → Optimize → Storage
```

## EXIF Orientation Correction

### EXIF Orientation Values

| Value | Transformation | Description |
|-------|---------------|-------------|
| 1 | None | Normal |
| 2 | Flip Horizontal | Mirror left-right |
| 3 | Rotate 180° | Half-turn |
| 4 | Flip Vertical | Mirror top-bottom |
| 5 | Transpose | Flip + rotate 90° CCW |
| 6 | Rotate 270° CW | Rotate 90° CW |
| 7 | Transverse | Flip + rotate 90° CW |
| 8 | Rotate 90° CW | Rotate 270° CCW |

### Usage

```python
from src.kernel.storage.image_processor import ImageProcessor

processor = ImageProcessor()

# Correct orientation
corrected, was_corrected = processor.fix_exif_orientation(image)
```

### Edge Cases

- **Missing EXIF:** Returns image unchanged
- **Corrupted EXIF:** Graceful fallback, returns original
- **Orientation = 1:** No transformation applied
- **Double-correction prevented:** EXIF orientation tag cleared after correction

## Resize

- **Downscale only** — never upscales
- **Aspect ratio preserved** by default
- **LANCZOS resampling** for high-quality downsampling
- Default max dimensions: 1920×1080

```python
resized = processor.resize_image(image, max_width=1920, max_height=1080)
```

## Optimization

### JPEG
- Quality tuning (default: 85)
- Progressive encoding
- Metadata stripping

### PNG
- Lossless optimization
- Compression level 9

```python
optimized_bytes = processor.optimize_image(image, quality=85, output_format="JPEG")
```

## End-to-End Pipeline

```python
result = processor.process_image_upload(file_bytes)
# Returns ImageProcessingResult with:
# - processed_bytes: optimized image data
# - original_width/height: dimensions before processing
# - processed_width/height: dimensions after processing
# - original_size_bytes / processed_size_bytes
# - compression_ratio
# - exif_corrected: bool
```

## Error Handling

- `InvalidImageError` — raised for non-image files or corrupted images
- Graceful handling of missing/corrupted EXIF data
- Tenant-scoped validation in S3 adapter layer

## Testing

Tests in `test/kernel/storage/test_image_processor.py`:
- All 8 EXIF orientation transformations
- Missing/corrupted EXIF handling
- Resize downscale/no-upscale/aspect-ratio
- JPEG/PNG optimization
- End-to-end pipeline
- Non-image file rejection