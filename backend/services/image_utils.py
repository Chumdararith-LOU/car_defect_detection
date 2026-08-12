import io
import numpy as np
from PIL import Image


def process_uploaded_image(contents: bytes) -> np.ndarray | None:
    """Converts raw bytes from the FastAPI upload into a numpy array."""
    if not contents or len(contents) < 100:
        return None
    try:
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        return np.array(image)
    except Exception as e:
        print(f"Image processing error: {e}")
        return None
