import cv2
from ultralytics import YOLO

class ElephantDetector:
    def __init__(self, model_path="yolov8n.pt", target_class="elephant", min_conf=0.50):
        self.model = YOLO(model_path)
        self.min_conf = min_conf
        self.target_class = target_class.lower()

    def process_frame(self, frame):
        results = self.model(frame, verbose=False)[0]
        detected_boxes = []

        for box in results.boxes:
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            label = self.model.names[cls_id].lower()

            if (label == self.target_class or "elephant" in label) and conf >= self.min_conf:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detected_boxes.append({
                    "bbox": (x1, y1, x2, y2),
                    "confidence": conf,
                    "label": label
                })

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 215, 255), 2)
                cv2.putText(
                    frame,
                    f"ELEPHANT {conf:.2f}",
                    (x1, max(20, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 215, 255),
                    2
                )

        return frame, detected_boxes
