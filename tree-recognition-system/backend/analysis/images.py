"""Decode uploads, remove metadata and measure image quality before inference."""
from dataclasses import dataclass
import hashlib
from io import BytesIO
import warnings

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError


ORGANS = {"auto", "leaf", "bark", "flower", "fruit"}
MAX_PIXELS = 24_000_000
MAX_FILE_BYTES = 10 * 1024 * 1024


@dataclass
class AnalysisImage:
    content: bytes
    organ: str
    quality: dict
    sha256: str


def prepare_image(content: bytes, organ: str) -> AnalysisImage:
    if organ not in ORGANS:
        raise ValueError("Rasm qismi auto, leaf, bark, flower yoki fruit bo'lishi kerak.")
    if not content or len(content) > MAX_FILE_BYTES:
        raise ValueError("Har bir rasm hajmi 10 MB dan oshmasligi kerak.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as original:
                if original.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValueError("JPEG, PNG yoki WebP rasm yuboring.")
                if original.width * original.height > MAX_PIXELS:
                    raise ValueError("Rasm 24 megapikseldan oshmasligi kerak.")
                if getattr(original, "n_frames", 1) != 1:
                    raise ValueError("Animatsiya o'rniga bitta rasm yuboring.")
                original.load()
                img = ImageOps.exif_transpose(original).convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        raise ValueError("Rasm ochilmadi. Buzilmagan JPEG, PNG yoki WebP yuboring.") from exc

    width, height = img.size
    digest = hashlib.sha256(f"{width}x{height}:".encode() + img.tobytes()).hexdigest()
    sample = img.copy()
    sample.thumbnail((1024, 1024))
    gray = cv2.cvtColor(np.asarray(sample), cv2.COLOR_RGB2GRAY)
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())
    contrast = float(gray.std())
    issues = []
    blocking = False
    if min(width, height) < 224:
        issues.append("Rasm juda kichik. Kamida 224 px, yaxshisi 800 px yoki kattaroq rasm oling.")
        blocking = True
    elif min(width, height) < 800:
        issues.append("Aniqroq tahlil uchun kamida 800 px rasm tavsiya etiladi.")
    if brightness < 25 or brightness > 235:
        issues.append("Yoritish yetarli emas yoki rasm haddan tashqari yorug'. Qayta suratga oling.")
        blocking = True
    if sharpness < 20 or contrast < 8:
        issues.append("Rasm xira yoki detallar yetarli emas. Fokusni daraxtga qarating.")
        blocking = True
    quality = {
        "width": width, "height": height, "sharpness": round(sharpness, 2),
        "brightness": round(brightness, 2), "contrast": round(contrast, 2),
        "status": "rejected" if blocking else "warning" if issues else "accepted",
        "issues": issues,
    }
    # Bound inference payloads; JPEG encoding omits EXIF/GPS metadata.
    img.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
    output = BytesIO()
    img.save(output, format="JPEG", quality=92)
    return AnalysisImage(output.getvalue(), organ, quality, digest)
