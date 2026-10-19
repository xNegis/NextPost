import io
import logging
import warnings
from dataclasses import dataclass

from PIL import Image, ImageCms, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener

register_heif_opener()

logger = logging.getLogger(__name__)

JPEG_QUALITY = 82

_ALLOWED_FORMATS = frozenset({"JPEG", "MPO", "PNG", "WEBP", "HEIF"})

# Reject decompression bombs before they allocate. The configured per-image
# pixel check below remains authoritative for the accepted limit.
Image.MAX_IMAGE_PIXELS = 400_000_000


class ImageProcessingError(Exception):
    """A bounded image could not be normalized, carrying a stable error code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class NormalizedImage:
    width: int
    height: int
    content: bytes


def _flatten_on_white(image: Image.Image) -> Image.Image:
    if image.mode == "RGB":
        return image
    rgba = image.convert("RGBA")
    background = Image.new("RGB", rgba.size, (255, 255, 255))
    background.paste(rgba, mask=rgba.getchannel("A"))
    return background


def _resize_to_max_edge(image: Image.Image, max_output_edge: int) -> Image.Image:
    width, height = image.size
    longest = max(width, height)
    if longest <= max_output_edge:
        return image
    scale = max_output_edge / longest
    new_size = (
        max(1, round(width * scale)),
        max(1, round(height * scale)),
    )
    return image.resize(new_size, Image.Resampling.LANCZOS)


def _convert_embedded_profile_to_srgb(image: Image.Image) -> Image.Image:
    profile = image.info.get("icc_profile")
    if not isinstance(profile, bytes) or not profile:
        return image

    has_alpha = "A" in image.getbands() or "transparency" in image.info
    alpha = image.convert("RGBA").getchannel("A") if has_alpha else None
    source = image.convert("RGB") if has_alpha else image
    try:
        converted = ImageCms.profileToProfile(
            source,
            ImageCms.ImageCmsProfile(io.BytesIO(profile)),
            ImageCms.createProfile("sRGB"),
            outputMode="RGB",
        )
    except (ImageCms.PyCMSError, OSError, ValueError) as exc:
        raise ImageProcessingError("invalid_image") from exc
    if converted is None:
        raise ImageProcessingError("invalid_image")
    if alpha is not None:
        converted.putalpha(alpha)
    return converted


def _is_animated_input(image: Image.Image) -> bool:
    """Distinguish still containers with companions from image sequences.

    The pillow-heif Pillow adapter exposes every top-level image as a frame, so
    ordinary iPhone HEIF containers with a primary photo plus companion images
    report ``is_animated`` even when their file brand is a still-image brand. An
    MPO similarly contains a primary JPEG plus one or more companion pictures;
    Safari can emit it when adapting an iPhone gallery photo for a restricted
    web picker. HEIF sequence brands remain animated input and are rejected.
    """
    if image.format == "HEIF":
        mimetype = getattr(image, "custom_mimetype", "")
        return isinstance(mimetype, str) and mimetype.endswith("-sequence")
    if image.format == "MPO":
        return False
    return bool(getattr(image, "is_animated", False) or getattr(image, "n_frames", 1) > 1)


def process_image(
    content: bytes,
    max_pixels: int,
    max_output_edge: int,
) -> NormalizedImage:
    """Validate and normalize one still image into a metadata-free sRGB JPEG.

    Raises ImageProcessingError with a stable code on rejection.
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            try:
                image = Image.open(io.BytesIO(content))
                image.load()
            except Image.DecompressionBombError as exc:
                raise ImageProcessingError("too_many_pixels") from exc
            except Image.DecompressionBombWarning as exc:
                raise ImageProcessingError("too_many_pixels") from exc
    except ImageProcessingError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as exc:
        raise ImageProcessingError("invalid_image") from exc

    if image.format not in _ALLOWED_FORMATS:
        logger.warning(
            "unsupported decoded image format: format=%s container_mimetype=%s frames=%s mode=%s",
            image.format,
            getattr(image, "custom_mimetype", None),
            getattr(image, "n_frames", 1),
            image.mode,
        )
        raise ImageProcessingError("unsupported_format")

    if _is_animated_input(image):
        raise ImageProcessingError("animated_input")

    width, height = image.size
    if width <= 0 or height <= 0:
        raise ImageProcessingError("invalid_image")
    if width * height > max_pixels:
        raise ImageProcessingError("too_many_pixels")

    oriented = ImageOps.exif_transpose(image)
    color_managed = _convert_embedded_profile_to_srgb(oriented)
    flattened = _flatten_on_white(color_managed)
    resized = _resize_to_max_edge(flattened, max_output_edge)

    final = Image.new("RGB", resized.size)
    final.paste(resized)

    output = io.BytesIO()
    final.save(output, format="JPEG", quality=JPEG_QUALITY)
    output.seek(0)
    final_bytes = output.read()

    with Image.open(io.BytesIO(final_bytes)) as verified:
        verified.load()
        if verified.format != "JPEG":
            raise ImageProcessingError("image_processing_failed")
        if verified.mode != "RGB" or verified.size != final.size:
            raise ImageProcessingError("image_processing_failed")

    return NormalizedImage(
        width=final.width,
        height=final.height,
        content=final_bytes,
    )
