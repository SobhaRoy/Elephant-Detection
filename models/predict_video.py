import os
import sys
import time
import cv2
import requests
from datetime import datetime, timezone

# Ensure Python locates models/detector.py regardless of execution directory
sys.path.append(os.path.dirname(__file__))
from detector import ElephantDetector

API_URL = "http://127.0.0.1:8000/detect"
ALERT_COOLDOWN_SECS = 8
last_alert_time = 0

detector = ElephantDetector(model_path="yolov8n.pt", min_conf=0.50)

# Check for sample drone video in videos/ directory, fallback to webcam
sample_video_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "videos", "elephant_drone_sample.mp4")

if os.path.exists(sample_video_path):
    print(f"Loading recorded drone feed: {sample_video_path}")
    cap = cv2.VideoCapture(sample_video_path)
else:
    print("No video file detected in videos/. Defaulting to webcam (0)...")
    cap = cv2.VideoCapture(0)

print("Inference active. Press 'q' on the preview window to exit.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        # Loop video if it reaches the end
        if os.path.exists(sample_video_path):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        break

    annotated_frame, detections = detector.process_frame(frame)
    elephant_count = len(detections)
    current_time = time.time()

    if elephant_count > 0:
        best_conf = max(d["confidence"] for d in detections)
        
        # Debounce to prevent flooding FastAPI per API contract
        if current_time - last_alert_time >= ALERT_COOLDOWN_SECS:
            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "latitude": 26.7271,
                "longitude": 88.3953,
                "confidence": round(best_conf, 2),
                "elephant_count": elephant_count,
                "source": "drone_01"
            }
            try:
                res = requests.post(API_URL, json=payload, timeout=2)
                if res.status_code == 200:
                    print(f"[ALERT TRANSMITTED] Herd: {elephant_count} | Conf: {best_conf:.2f}")
                    last_alert_time = current_time
            except Exception as err:
                print(f"[TRANSMISSION ERROR]: {err}")
        else:
            remaining = int(ALERT_COOLDOWN_SECS - (current_time - last_alert_time))
            cv2.putText(annotated_frame, f"COOLDOWN: {remaining}s", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

    cv2.imshow("EleGuard AI - Surveillance Feed", annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
