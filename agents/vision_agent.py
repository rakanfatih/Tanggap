from vision.image_validator import validate_image
from vision.yolo_detector import detect_objects
from vision.flood_analyzer import analyze_flood
from vision.fake_detector import detect_fake
from vision.vision_schema import VisionOutput
from vision.water_analyzer import analyze_water
from vision.vehicle_immersion import analyze_vehicle_immersion
from vision.water_level_estimator import estimate_water_level


def analyze_image(image_path: str):

    print("\n==============================")
    print("[VISION AGENT]")
    print("==============================")

    validate_image(image_path)

    detections = detect_objects(image_path)
    water_result = analyze_water(image_path)

    immersion_result = analyze_vehicle_immersion(
        image_path,
        detections
    )

    water_level_result = estimate_water_level(
    image_path,
    detections
    )

    flood = analyze_flood(
        detections,
        water_result,
        immersion_result,
        water_level_result
        )
    
    fake = detect_fake(detections)

    hasil = VisionOutput(
        flood_detected=flood["flood_detected"],
        confidence=flood["confidence"],
        severity=flood["severity"],
        estimated_water_level=flood["estimated_water_level"],
        estimated_water_cm=flood["estimated_water_cm"],
        water_percentage=flood["water_percentage"],
        visible_objects=flood["visible_objects"],
        object_count=flood["object_count"],
        image_quality="Baik",
        possible_fake=fake["possible_fake"],
        reason=fake["reason"]
    )

    return hasil