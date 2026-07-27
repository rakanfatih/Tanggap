import cv2

def analyze_water(mask, image_shape):

    water_pixels = cv2.countNonZero(mask)
    total_pixels = image_shape[0] * image_shape[1]
    percentage = (water_pixels / total_pixels) * 100

    if percentage >= 45:
        level = "Tinggi"
    elif percentage >= 25:
        level = "Sedang"
    elif percentage >= 8:
        level = "Rendah"
    else:
        level = "Tidak Ada"

    return {
        "water_percentage": round(percentage, 2),
        "water_level": level
    }