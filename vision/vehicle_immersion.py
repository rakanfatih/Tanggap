import cv2

VEHICLES = ["car", "truck", "bus", "motorcycle"]

def analyze_vehicle_immersion(water_mask, detections):

    immersion_result = []

    for obj in detections:

        if obj["label"] not in VEHICLES:
            continue

        x1, y1, x2, y2 = obj["bbox"]
        height = y2 - y1

        if height <= 0:
            continue

        start_y = int(y1 + height * 0.60)
        roi = water_mask[start_y:y2, x1:x2] 
        
        if roi.size == 0:
            continue
            
        water_pixels = cv2.countNonZero(roi)
        total_pixels = roi.shape[0] * roi.shape[1]
        percentage = (water_pixels / total_pixels) * 100
        submerged = percentage >= 50
        
        immersion_result.append({
            "vehicle": obj["label"],
            "water_percentage": round(percentage, 2),
            "submerged": submerged
        })

    return immersion_result