from collections import Counter

URBAN_OBJECTS = [
    "car", "motorcycle", "bus", "truck", "bicycle",
    "fire hydrant", "stop sign", "parking meter", "bench", "traffic light"
]

def analyze_flood(
        detections,
        water_result,
        immersion_result,
        water_level_result
        ):

    labels = [
        d["label"]
        for d in detections
    ]

    counter = Counter(labels)
    person = counter.get("person", 0)
    boat = counter.get("boat", 0)
    
    water_percentage = water_result["water_percentage"]

    score = water_percentage * 1.5

    if boat > 0:
        score += 15

    if person > 0:
        score += 5

    submerged_vehicles = 0
    for vehicle in immersion_result:
        if vehicle["submerged"]:
            score += 15
            submerged_vehicles += 1

    estimated_cm = water_level_result["estimated_cm"] 
    has_urban_objects = any(label in URBAN_OBJECTS for label in labels)

    if estimated_cm == 0 and submerged_vehicles == 0 and boat == 0:
        score = min(score, 70.0)
    elif not has_urban_objects and submerged_vehicles == 0:
        score = min(score, 70.0)
    else:
        score = min(score, 100.0)

    if score >= 75:
        severity = "Tinggi"
    elif score >= 40:
        severity = "Sedang"
    elif score >= 20:
        severity = "Rendah"
    else:
        severity = "Tidak Terdeteksi"

    flood_detected = score >= 20 or water_percentage >= 10

    return {
        "flood_detected": flood_detected,
        "confidence": round(score, 2),
        "severity": severity,
        "estimated_water_level": water_level_result["level"],
        "estimated_water_cm": water_level_result["estimated_cm"],
        "water_percentage": water_percentage,
        "visible_objects": list(counter.keys()),
        "object_count": len(labels)
    }