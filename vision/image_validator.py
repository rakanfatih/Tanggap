import os
import cv2

VALID_EXTENSIONS = [
    ".jpg",
    ".jpeg",
    ".png"
]

def validate_image(image_path: str):

    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Gambar tidak ditemukan : {image_path}"
        )

    ext = os.path.splitext(image_path)[1].lower()

    if ext not in VALID_EXTENSIONS:
        raise ValueError(
            "Format gambar tidak didukung."
        )

    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(
            "Gagal membaca gambar."
        )

    h, w = image.shape[:2]
    if h < 200 or w < 200:
        raise ValueError(
            "Resolusi gambar terlalu kecil."
        )
    return {"valid": True, "image": image, "width": w, "height": h}