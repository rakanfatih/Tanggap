import os
import cv2
import numpy as np
from ultralytics import YOLO

from vision.image_validator import validate_image
from vision.yolo_detector import detect_objects
from vision.flood_analyzer import analyze_flood
from vision.fake_detector import detect_fake
from vision.vision_schema import VisionOutput
from vision.water_analyzer import analyze_water
from vision.vehicle_immersion import analyze_vehicle_immersion
from vision.water_level_estimator import estimate_water_level

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "best_water_seg.pt")

try:
    model_seg = YOLO(MODEL_PATH)
    print(f"[VISION] Model segmentasi berhasil dimuat")
except Exception as e:
    print(f"[VISION] GAGAL load model segmentasi: {e}")
    model_seg = None 
    
def analyze_image(image_path: str):
    print("\n==============================")
    print("[VISION AGENT]")
    print("==============================")

    val_result = validate_image(image_path)
    image = val_result["image"] 
    h, w = image.shape[:2]

    water_mask = np.zeros((h, w), dtype=np.uint8)

    if model_seg is not None:
        seg_results = model_seg.predict(image, conf=0.25, verbose=False)
        
        if seg_results[0].masks is not None:
            masks_data = seg_results[0].masks.data.cpu().numpy()
            boxes_data = seg_results[0].boxes.xyxy.cpu().numpy()
            
            for i, mask in enumerate(masks_data):
                y1 = boxes_data[i][1]
                y2 = boxes_data[i][3]
                
                center_y = (y1 + y2) / 2
                
                if center_y < (h / 2):
                    continue
                
                if y1 < (h * 0.05) and y2 < (h * 0.7):
                    continue
                    
                m_resized = cv2.resize(mask, (w, h))
                water_mask = cv2.bitwise_or(water_mask, (m_resized * 255).astype(np.uint8))

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
    annotated_image = image.copy()

    if cv2.countNonZero(water_mask) > 0:
        colored_mask = np.zeros_like(annotated_image)
        colored_mask[:, :] = [255, 0, 0] 
        
        mask_bool = water_mask > 0
        
        annotated_image[mask_bool] = cv2.addWeighted(
            annotated_image[mask_bool], 0.6,
            colored_mask[mask_bool], 0.4, 0
        )

    for obj in detections:
        x1, y1, x2, y2 = obj["bbox"]
        label = obj["label"]
        conf = obj["confidence"]
        
        cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        text = f"{label} {conf:.2f}"
        cv2.putText(annotated_image, text, (x1, max(15, y1 - 10)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    base_name = os.path.basename(image_path)
    name, ext = os.path.splitext(base_name)
    vision_filename = f"{name}_vision{ext}" 
    
    vision_image_path = os.path.join(os.path.dirname(image_path), vision_filename)
    cv2.imwrite(vision_image_path, annotated_image)

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
        reason=fake["reason"],
        vision_image_path=vision_image_path
    )

    print("\n===== HASIL VISION =====")
    print(f"Flood Detected   : {hasil.flood_detected}")
    print(f"Confidence       : {hasil.confidence}")
    print(f"Severity         : {hasil.severity}")
    print(f"Water Level      : {hasil.estimated_water_level}")
    print(f"Estimated Water  : {hasil.estimated_water_cm} cm ({hasil.estimated_water_level})")
    print(f"Water Area       : {hasil.water_percentage} %")
    print(f"Objects Found    : {hasil.object_count} {hasil.visible_objects}")
    print(f"Possible Fake    : {hasil.possible_fake}")
    print(f"Reason           : {hasil.reason}")
    print("=========================")

    return hasil