from ultralytics import YOLO

model = YOLO("yolov8n.pt")


def detect_objects(image_path):

    results = model.predict(
        image_path,
        verbose=False
    )

    detections = []

    for result in results:
        names = result.names

        for box in result.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])

            xyxy = box.xyxy[0].tolist()

            detections.append({
                "label": names[cls],
                "confidence": round(conf,3),
                "bbox": [
                    int(xyxy[0]),
                    int(xyxy[1]),
                    int(xyxy[2]),
                    int(xyxy[3])
                ]
            })

    return detections