import io

import pytest
from PIL import Image, ImageCms

from app.imaging import ImageProcessingError, process_image

MAX_PIXELS = 40000000
MAX_EDGE = 2560


def _bytes(image: Image.Image, **kwargs) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, **kwargs)
    return buffer.getvalue()


def _jpeg(size=(100, 80), color=(200, 30, 30)) -> bytes:
    return _bytes(Image.new("RGB", size, color), format="JPEG", quality=90)


def _jpeg_with_exif(orientation: int, gps: bool = True) -> bytes:
    image = Image.new("RGB", (40, 60), (20, 120, 220))
    exif = Image.Exif()
    exif[274] = orientation
    if gps:
        exif[34853] = {1: "N", 2: (40.0, 26.0, 0.0), 3: "W", 4: (29.0, 58.0, 0.0)}
    image.info["comment"] = b"should not survive"
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90, exif=exif)
    return buffer.getvalue()


def _webp(size=(64, 64), animated: bool = False) -> bytes:
    image = Image.new("RGB", size, (40, 200, 90))
    if not animated:
        return _bytes(image, format="WEBP")
    frames = [image, Image.new("RGB", size, (200, 40, 90))]
    return _bytes(image, format="WEBP", save_all=True, append_images=frames)


def _png_with_alpha() -> bytes:
    image = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    for x in range(20):
        for y in range(40):
            image.putpixel((x, y), (10, 20, 30, 128))
    return _bytes(image, format="PNG")


def _heif() -> bytes:
    image = Image.new("RGB", (48, 32), (180, 90, 30))
    return _bytes(image, format="HEIF")


def _heif_with_companion_image(*, sequence: bool = False) -> bytes:
    first = Image.new("RGB", (48, 32), (180, 90, 30))
    primary = Image.new("RGB", (24, 16), (30, 90, 180))
    content = bytearray(
        _bytes(
            first,
            format="HEIF",
            save_all=True,
            append_images=[primary],
            primary_index=1,
        )
    )
    if sequence:
        # Switch the HEIC still-image major brand to its sequence equivalent.
        content[8:12] = b"hevc"
    return bytes(content)


def _mpo() -> bytes:
    primary = Image.new("RGB", (60, 40), (180, 90, 30))
    companion = Image.new("RGB", (30, 20), (30, 90, 180))
    return _bytes(primary, format="MPO", save_all=True, append_images=[companion])


def _decoded(content: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(content))
    image.load()
    return image


def test_jpeg_round_trips_without_metadata() -> None:
    result = process_image(_jpeg(), MAX_PIXELS, MAX_EDGE)

    assert (result.width, result.height) == (100, 80)
    decoded = _decoded(result.content)
    assert decoded.format == "JPEG"
    assert decoded.mode == "RGB"
    assert decoded.getexif().get(274) in (None, 1)
    assert list(decoded.getexif().items()) == []


def test_heic_and_heif_decode_to_jpeg() -> None:
    result = process_image(_heif(), MAX_PIXELS, MAX_EDGE)

    assert (result.width, result.height) == (48, 32)
    assert _decoded(result.content).format == "JPEG"


def test_heif_with_companion_images_uses_the_primary_still() -> None:
    result = process_image(_heif_with_companion_image(), MAX_PIXELS, MAX_EDGE)

    assert (result.width, result.height) == (24, 16)
    assert _decoded(result.content).format == "JPEG"


def test_heif_image_sequence_is_rejected() -> None:
    with pytest.raises(ImageProcessingError) as exc:
        process_image(_heif_with_companion_image(sequence=True), MAX_PIXELS, MAX_EDGE)
    assert exc.value.code == "animated_input"


def test_mpo_uses_the_primary_jpeg_and_discards_companion_images() -> None:
    result = process_image(_mpo(), MAX_PIXELS, MAX_EDGE)

    assert (result.width, result.height) == (60, 40)
    decoded = _decoded(result.content)
    assert decoded.format == "JPEG"
    assert getattr(decoded, "n_frames", 1) == 1


def test_exif_orientation_is_applied() -> None:
    content = _jpeg_with_exif(6, gps=False)
    result = process_image(content, MAX_PIXELS, MAX_EDGE)

    # 40x60 rotated 90 degrees clockwise becomes 60x40.
    assert (result.width, result.height) == (60, 40)


def test_gps_and_comment_metadata_are_stripped() -> None:
    result = process_image(_jpeg_with_exif(1), MAX_PIXELS, MAX_EDGE)

    decoded = _decoded(result.content)
    assert 34853 not in decoded.getexif()
    assert not decoded.info.get("comment")


def test_embedded_color_profile_is_converted_and_not_copied() -> None:
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    content = _bytes(
        Image.new("RGB", (32, 24), (30, 80, 160)),
        format="JPEG",
        quality=90,
        icc_profile=profile,
    )

    result = process_image(content, MAX_PIXELS, MAX_EDGE)
    decoded = _decoded(result.content)

    assert decoded.mode == "RGB"
    assert "icc_profile" not in decoded.info


def test_transparency_is_flattened_on_white() -> None:
    result = process_image(_png_with_alpha(), MAX_PIXELS, MAX_EDGE)
    decoded = _decoded(result.content)

    assert decoded.mode == "RGB"
    transparent = decoded.getpixel((30, 20))
    # JPEG is lossy, so the flattened background is white within tolerance.
    assert all(channel >= 250 for channel in transparent)


def test_output_edge_is_capped_without_upscaling() -> None:
    large = _bytes(Image.new("RGB", (5000, 100), (10, 10, 10)), format="JPEG", quality=90)
    result = process_image(large, MAX_PIXELS, 2560)

    assert max(result.width, result.height) == 2560
    assert (result.width, result.height) == (2560, 51)

    small = process_image(_jpeg((100, 80)), MAX_PIXELS, 2560)
    assert (small.width, small.height) == (100, 80)


def test_webp_is_accepted() -> None:
    result = process_image(_webp(), MAX_PIXELS, MAX_EDGE)
    assert (result.width, result.height) == (64, 64)


def test_animated_webp_is_rejected() -> None:
    with pytest.raises(ImageProcessingError) as exc:
        process_image(_webp(animated=True), MAX_PIXELS, MAX_EDGE)
    assert exc.value.code == "animated_input"


def test_unsupported_format_is_rejected() -> None:
    gif = _bytes(Image.new("RGB", (10, 10)), format="GIF")
    with pytest.raises(ImageProcessingError) as exc:
        process_image(gif, MAX_PIXELS, MAX_EDGE)
    assert exc.value.code == "unsupported_format"


def test_corrupt_input_is_rejected() -> None:
    with pytest.raises(ImageProcessingError) as exc:
        process_image(b"definitely not an image", MAX_PIXELS, MAX_EDGE)
    assert exc.value.code == "invalid_image"


def test_truncated_jpeg_is_rejected() -> None:
    content = _jpeg()
    with pytest.raises(ImageProcessingError) as exc:
        process_image(content[: len(content) // 2], MAX_PIXELS, MAX_EDGE)
    assert exc.value.code == "invalid_image"


def test_too_many_pixels_is_rejected() -> None:
    content = _jpeg((400, 400))
    with pytest.raises(ImageProcessingError) as exc:
        process_image(content, max_pixels=100000, max_output_edge=MAX_EDGE)
    assert exc.value.code == "too_many_pixels"
