import cv2
import numpy as np


REFERENCE_OBJECTS = {
    "person": 170,
    "car": 150,
    "bus": 320,
    "truck": 340,
    "motorcycle": 110
}

def estimate_water_level(image_path, detections):

    image = cv2.imread(image_path)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower = np.array([0, 0, 40])
    upper = np.array([180, 90, 220])
    mask = cv2.inRange(hsv, lower, upper)

    estimates = []

    for obj in detections:

        label = obj["label"]

        if label not in REFERENCE_OBJECTS:
            continue

        x1, y1, x2, y2 = obj["bbox"]
        object_height = y2 - y1

        if object_height <= 0:
            continue

        roi = mask[y1:y2, x1:x2]
        rows = roi.shape[0]
        submerged = 0

        # hitung dari bawah ke atas
        for i in range(rows - 1, -1, -1):
            row = roi[i]
            white = cv2.countNonZero(row)

            if white > row.shape[0] * 0.5:
                submerged += 1
            else:
                break

        ratio = submerged / object_height
        real_height = REFERENCE_OBJECTS[label]
        estimated_cm = ratio * real_height
        estimates.append({
            "object": label,
            "ratio": round(ratio, 2),
            "estimated_cm": round(estimated_cm, 1)
        })

    if len(estimates) == 0:
        return {
            "estimated_cm": 0,
            "level": "Tidak diketahui",
            "detail": []
        }

    max_height = max(x["estimated_cm"] for x in estimates)

    if max_height >= 100:
        level = ">100 cm"

    elif max_height >= 30:
        level = "30-100 cm"

    elif max_height > 0:
        level = "<30 cm"

    else:
        level = "Tidak diketahui"

    return {
        "estimated_cm": round(max_height, 1),
        "level": level,
        "detail": estimates
    }