from collections import Counter

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
    car = counter.get("car", 0)
    bus = counter.get("bus", 0)
    truck = counter.get("truck", 0)
    boat = counter.get("boat", 0)
    motorcycle = counter.get("motorcycle", 0)
    water_percentage = water_result["water_percentage"]

    score = 0

    # boat hampir pasti banjir
    score += boat * 30
    # orang terlihat di lokasi
    score += min(person * 5, 20)
    # kendaraan
    score += min(car * 3, 15)
    score += min(bus * 5, 10)
    score += min(truck * 5, 10)
    score += min(motorcycle * 3, 10)
    # kontribusi luas genangan
    score += min(water_percentage, 40)

    if boat > 0 and person > 0:
        score += 15

    if boat > 0 and car > 0:
        score += 10

    if person > 2 and car > 2:
        score += 10

    for vehicle in immersion_result:

        if vehicle["submerged"]:
            score += 20

    if water_percentage > 30:
            score += 15

    if water_percentage > 50:
            score += 20

    score = min(score, 100)

    if score >= 70:
        severity = "Tinggi"

    elif score >= 40:
        severity = "Sedang"

    elif score >= 20:
        severity = "Rendah"

    else:
        severity = "Tidak Terdeteksi"

    flood_detected = score >= 20

    return {
        "flood_detected": flood_detected,
        "confidence": round(score,2),
        "severity": severity,
        "estimated_water_level": water_level_result["level"],
        "estimated_water_cm": water_level_result["estimated_cm"],
        "water_percentage": water_result["water_percentage"],
        "visible_objects": list(counter.keys()),
        "object_count": len(labels)
    }