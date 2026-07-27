import cv2
import numpy as np
from vision.image_validator import validate_image
from vision.yolo_detector import detect_objects
from vision.flood_analyzer import analyze_flood
from vision.fake_detector import detect_fake
from vision.vision_schema import VisionOutput
from vision.water_analyzer import analyze_water
from vision.vehicle_immersion import analyze_vehicle_immersion
from vision.water_level_estimator import estimate_water_level

WATER_HSV_LOWER = np.array([0, 0, 40])
WATER_HSV_UPPER = np.array([180, 90, 220])

def analyze_image(image_path: str):

    print("\n==============================")
    print("[VISION AGENT]")
    print("==============================")

    val_result = validate_image(image_path)
    image = val_result["image"] 

    hsv = cv2.cvtColor(
        image, 
        cv2.COLOR_BGR2HSV
        )
    
    water_mask = cv2.inRange(
        hsv, 
        WATER_HSV_LOWER, 
        WATER_HSV_UPPER
        )

    kernel = np.ones(
        (5, 5), 
        np.uint8
        )
    
    water_mask = cv2.morphologyEx(
        water_mask, 
        cv2.MORPH_OPEN, 
        kernel
        )
    
    water_mask = cv2.morphologyEx(
        water_mask, 
        cv2.MORPH_CLOSE, 
        kernel
        )

    detections = detect_objects(image)

    water_result = analyze_water(
        water_mask, 
        image.shape
        )
    
    immersion_result = analyze_vehicle_immersion(
        water_mask, 
        detections
        )
    
    water_level_result = estimate_water_level(
        water_mask, 
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


    print("\n===== HASIL VISION =====")
    print(f"Flood Detected   : {hasil.flood_detected}")
    print(f"Confidence       : {hasil.confidence}")
    print(f"Severity         : {hasil.severity}")
    print(f"Estimated Water  : {hasil.estimated_water_cm} cm ({hasil.estimated_water_level})")
    print(f"Water Area       : {hasil.water_percentage} %")
    print(f"Objects Found    : {hasil.object_count} {hasil.visible_objects}")
    print(f"Possible Fake    : {hasil.possible_fake}")
    print(f"Reason           : {hasil.reason}")
    print("=========================")

    return hasil