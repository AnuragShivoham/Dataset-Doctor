"""Discover and safely inspect supported image files without modifying them."""

from pathlib import Path

from PIL import Image, UnidentifiedImageError

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def discover_images(source: str | Path) -> tuple[list[Path], list[Path]]:
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"Image dataset not found: {path}")
    if path.is_file():
        return ([path] if path.suffix.lower() in SUPPORTED_EXTENSIONS else [],
                [] if path.suffix.lower() in SUPPORTED_EXTENSIONS else [path])
    files = sorted(item for item in path.rglob("*") if item.is_file())
    supported = [item for item in files if item.suffix.lower() in SUPPORTED_EXTENSIONS]
    unsupported = [item for item in files if item.suffix.lower() not in SUPPORTED_EXTENSIONS]
    return supported, unsupported


def inspect_image(path: str | Path) -> dict:
    """Return metadata or a structured decode error. Image bytes are only read."""
    path = Path(path)
    record = {"path": str(path), "filename": path.name, "extension": path.suffix.lower(),
              "file_size": path.stat().st_size, "width": None, "height": None,
              "mode": None, "channels": None, "readable": False, "error": None}
    if record["file_size"] == 0:
        record["error"] = "zero_byte"
        return record
    try:
        with Image.open(path) as image:
            image.load()
            record.update(width=int(image.width), height=int(image.height), mode=image.mode,
                          channels=len(image.getbands()), readable=image.width > 0 and image.height > 0)
            if not record["readable"]:
                record["error"] = "invalid_dimensions"
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as exc:
        record["error"] = "decode_error"
        record["error_detail"] = str(exc)[:200]
    return record
