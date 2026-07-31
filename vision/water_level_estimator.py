import cv2

# perkiraan tinggi objek
REFERENCE_OBJECTS = {
    "person": 170,
    "car": 150,
    "bus": 320,
    "truck": 340,
    "motorcycle": 110
}

ROW_WET_THRESHOLD = 0.3
MAX_DRY_GAP = 3

def estimate_water_level(water_mask, detections):
    estimates = []

    for obj in detections:
        label = obj["label"]
        if label not in REFERENCE_OBJECTS:
            continue

        x1, y1, x2, y2 = obj["bbox"]
        object_height = y2 - y1

        if object_height <= 0:
            continue

        h, w = water_mask.shape
        roi_y1 = max(0, y1)
        roi_y2 = min(h, y2)
        roi_x1 = max(0, x1 - 10)
        roi_x2 = min(w, x2 + 10)

        roi = water_mask[roi_y1:roi_y2, roi_x1:roi_x2]
        rows = roi.shape[0]
        
        if rows == 0:
            continue
            
        submerged = 0
        dry_gap = 0

        for i in range(rows - 1, -1, -1):
            row = roi[i]
            white = cv2.countNonZero(row)

            if white > row.shape[0] * ROW_WET_THRESHOLD:
                submerged += 1 + dry_gap  
                dry_gap = 0
            else:
                dry_gap += 1
                if dry_gap > MAX_DRY_GAP:
                    break

        ratio = submerged / object_height
        
        ratio = min(ratio, 1.0)
        
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