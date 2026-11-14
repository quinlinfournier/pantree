import uuid
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps 
from pillow_heif import register_heif_opener; register_heif_opener()

RECEIPT_PIC_DIR = Path("media/upload")

def process_receipt_image(content: bytes) -> str:
    with Image.open(BytesIO(content)) as original:
        img = ImageOps.exif_transpose(original)

        img.thumbnail((2000, 2000))

        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

        filename = f"{uuid.uuid4().hex}.jpg"
        filepath = RECEIPT_PIC_DIR / filename

        RECEIPT_PIC_DIR.mkdir(parents=True, exist_ok=True)

        img.save(filepath, "JPEG", quality=85, optimize=True)

    return filename

def delete_receipt_image(filename: str | None) -> None:
    if filename is None:
        return

    filepath = RECEIPT_PIC_DIR / filename
    if filepath.exists():
        filepath.unlink()