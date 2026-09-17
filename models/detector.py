import cv2
from ultralytics import YOLO

class ElephantDetector:
    def __init__(self, model_path="yolov8n.pt", min_conf=0.25):
        self.model = YOLO(model_path)
        self.min_conf = min_conf
        # In COCO dataset, index 20 is 'elephant'
        self.elephant_class_id = 20

    def process_frame(self, frame):
        # Run inference
        results = self.model(frame, verbose=False, conf=self.min_conf)[0]
        detected_boxes = []

        for box in results.boxes:
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            label = self.model.names[cls_id].lower()

            # Check both class ID 20 and name 'elephant'
            if (cls_id == self.elephant_class_id or "elephant" in label) and conf >= self.min_conf:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detected_boxes.append({
                    "bbox": (x1, y1, x2, y2),
                    "confidence": conf,
                    "label": label
                })

                # High-visibility neon border
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
                cv2.putText(
                    frame,
                    f"ELEPHANT {int(conf * 100)}%",
                    (x1, max(25, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2
                )

        # Draw real-time HUD tracker on top of the video feed
        status_text = f"TRACKING: {len(detected_boxes)} ELEPHANT(S)" if detected_boxes else "SEARCHING FOR ELEPHANT..."
        status_color = (0, 255, 0) if detected_boxes else (0, 165, 255)
        cv2.putText(frame, status_text, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

        return frame, detected_boxes
