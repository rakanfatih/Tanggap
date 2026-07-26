import cv2
import numpy as np


def analyze_water(image_path):

    image = cv2.imread(image_path)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # air keruh / abu / coklat
    lower = np.array([0, 0, 40])
    upper = np.array([180, 90, 220])
    mask = cv2.inRange(hsv, lower, upper)
    kernel = np.ones((5,5),np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    water_pixels = cv2.countNonZero(mask)
    total_pixels = image.shape[0] * image.shape[1]
    percentage = (water_pixels / total_pixels) * 100

    if percentage >= 45:
        level = "Tinggi"

    elif percentage >= 25:
        level = "Sedang"

    elif percentage >= 8:
        level = "Rendah"

    else:
        level = "Tidak Ada"

    cv2.imwrite(
        "water_mask.jpg",
        mask
    )

    return {
        "water_percentage": round(percentage,2),
        "water_level": level,
        "mask": mask
    }