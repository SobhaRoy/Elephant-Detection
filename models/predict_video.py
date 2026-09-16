import cv2
import time
import requests
import numpy as np
from ultralytics import YOLO

# Load model
model = YOLO("yolov8n.pt")

ELEPHANT_CLASS_ID = 20
BACKEND_URL = "http://127.0.0.1:8000/detect"

# Base coordinates for Sevoke-Gulma corridor belt
BASE_LAT = 26.7271
BASE_LON = 88.3953

# Build gamma correction lookup table
GAMMA = 1.8
INV_GAMMA = 1.0 / GAMMA
GAMMA_TABLE = np.array([((i / 255.0) ** INV_GAMMA) * 255 for i in np.arange(256)]).astype("uint8")

# Initialize adaptive histogram equalizer
CLAHE = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))

def apply_night_vision(frame):
    """Enhance low-light frames using gamma boost + LAB-channel CLAHE."""
    brightened = cv2.LUT(frame, GAMMA_TABLE)
    lab = cv2.cvtColor(brightened, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l_enhanced = CLAHE.apply(l)
    enhanced_lab = cv2.merge((l_enhanced, a, b))
    return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

def run_vision_stream(source=0):
    cap = cv2.VideoCapture(source)
    last_alert_time = 0
    COOLDOWN_SECONDS = 3
    night_mode = True

    print("=== EleGuard AI - Vision Stream Active ===")
    print(" [n] Toggle Night-Vision Enhancement")
    print(" [q] Exit")

    prev_frame_time = time.time()

    while cap.isOpened():
        success, raw_frame = cap.read()
        if not success:
            break

        processed_frame = apply_night_vision(raw_frame) if night_mode else raw_frame
        results = model(processed_frame, verbose=False)[0]
        elephant_boxes = [b for b in results.boxes if int(b.cls[0]) == ELEPHANT_CLASS_ID]
        count = len(elephant_boxes)

        if count > 0:
            best_conf = max(float(b.conf[0]) for b in elephant_boxes)
            current_time = time.time()
            if current_time - last_alert_time >= COOLDOWN_SECONDS:
                payload = {
                    "latitude": BASE_LAT,
                    "longitude": BASE_LON,
                    "confidence": round(best_conf, 2),
                    "elephant_count": count,
                    "source": "drone_ir_night_feed" if night_mode else "drone_day_feed"
                }
                try:
                    res = requests.post(BACKEND_URL, json=payload, timeout=2)
                    print(f"[{payload['source'].upper()}] Herd: {count} | Conf: {best_conf:.2f} | Status: {res.status_code}")
                    last_alert_time = current_time
                except Exception as e:
                    print(f"[WARN] Backend dispatch failed: {e}")

        display_frame = results.plot()

        curr_time = time.time()
        fps = 1.0 / (curr_time - prev_frame_time) if (curr_time - prev_frame_time) > 0 else 30
        prev_frame_time = curr_time

        mode_text = "NIGHT VISION: [ON]" if night_mode else "NIGHT VISION: [OFF]"
        mode_color = (0, 255, 0) if night_mode else (0, 165, 255)
        cv2.putText(display_frame, mode_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, mode_color, 2)
        cv2.putText(display_frame, f"FPS: {fps:.1f}", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.imshow("EleGuard AI - Tactical Corridor Camera", display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('n'):
            night_mode = not night_mode
            print(f"[*] Night-Vision Mode switched to: {night_mode}")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_vision_stream(0)
