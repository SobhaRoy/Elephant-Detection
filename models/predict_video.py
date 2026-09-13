import cv2
import time
import requests
from ultralytics import YOLO

# 1. Load pretrained lightweight YOLOv8 nano model
model = YOLO("yolov8n.pt")

# COCO dataset class index for elephant is 20
ELEPHANT_CLASS_ID = 20
BACKEND_URL = "http://127.0.0.1:8000/detect"

# Coordinated corridor simulation (Sevoke-Gulma fringe)
SAMPLE_LATITUDE = 26.7271
SAMPLE_LONGITUDE = 88.3953

def run_vision_stream(source=0):
    """
    source can be:
    - 0 for laptop webcam
    - path to a video file: 'videos/drone_footage.mp4'
    """
    cap = cv2.VideoCapture(source)
    last_alert_time = 0
    COOLDOWN_SECONDS = 3  # Avoid network saturation on continuous frames

    print("=== EleGuard AI - YOLOv8 Vision Pipeline Active ===")
    print("Press 'q' in the video window to quit.")

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # Run YOLO inference
        results = model(frame, verbose=False)[0]
        elephant_boxes = [box for box in results.boxes if int(box.cls[0]) == ELEPHANT_CLASS_ID]
        count = len(elephant_boxes)

        if count > 0:
            best_confidence = max(float(box.conf[0]) for box in elephant_boxes)
            current_time = time.time()

            # Push alert payload if cooldown period has passed
            if current_time - last_alert_time >= COOLDOWN_SECONDS:
                payload = {
                    "latitude": SAMPLE_LATITUDE,
                    "longitude": SAMPLE_LONGITUDE,
                    "confidence": round(best_confidence, 2),
                    "elephant_count": count,
                    "source": "drone_alpha_vision"
                }
                try:
                    res = requests.post(BACKEND_URL, json=payload, timeout=2)
                    print(f"[VISION ALERT SENT] Detected: {count} elephant(s) | Conf: {best_confidence:.2f} | Status: {res.status_code}")
                    last_alert_time = current_time
                except Exception as e:
                    print(f"[ERROR] Could not dispatch to backend: {e}")

        # Draw bounding boxes and confidence on frame
        annotated_frame = results.plot()
        cv2.imshow("EleGuard AI - Live Aerial Detection Stream", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_vision_stream(0)
