from io import BytesIO

from PIL import Image


def make_test_image_bytes(color: tuple[int, int, int] = (90, 120, 180)) -> bytes:
    image = Image.new("RGB", (96, 64), color=color)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
