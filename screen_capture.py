import mss
import numpy as np
from PIL import Image
import base64
import io


def capture_screen() -> Image.Image:
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        raw = sct.grab(monitor)
        return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")


def image_to_base64(img: Image.Image, max_width: int = 1280) -> str:
    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def capture_region(x: int, y: int, w: int, h: int) -> Image.Image:
    with mss.mss() as sct:
        region = {"top": y, "left": x, "width": w, "height": h}
        raw = sct.grab(region)
        return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
