"""Image decoding and validation utilities."""
import cv2
import numpy as np


class ImageDecodeError(ValueError):
    """Raised when an uploaded payload cannot be decoded as an image."""


def decode_image(contents: bytes) -> np.ndarray:
    """Decode raw uploaded bytes into an RGB ``np.ndarray`` (H, W, 3).

    Raises ``ImageDecodeError`` if the payload is not a decodable image.
    """
    if not contents:
        raise ImageDecodeError("Empty upload")
    arr = np.frombuffer(contents, dtype=np.uint8)
    img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise ImageDecodeError("Could not decode image bytes")
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
