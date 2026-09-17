import os
import sys
import time
import cv2
import requests
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.database import engine, Base
from backend.routes import router
from backend.email_service import send_elephant_email_alert, get_email_logs
from models.detector import ElephantDetector

Base.metadata.create_all(bind=engine)

app = FastAPI(title="EleGuard AI - Tactical Wildlife Operations")
app.include_router(router)

FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/dashboard")
def serve_dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/sms_logs")
def get_dispatches():
    # Feeds the dispatch tab in the dashboard
    return JSONResponse(content=get_email_logs())

# Initialize YOLOv8 Detector
detector = ElephantDetector(model_path="yolov8n.pt", min_conf=0.25)
last_auto_alert = 0
ALERT_COOLDOWN = 6

def generate_annotated_feed():
    global last_auto_alert
    cap = cv2.VideoCapture(0)
    
    while True:
        success, frame = cap.read()
        if not success:
            break

        annotated_frame, detections = detector.process_frame(frame)
        count = len(detections)
        now = time.time()

        if count > 0 and (now - last_auto_alert >= ALERT_COOLDOWN):
            best_conf = max(d["confidence"] for d in detections)
            try:
                resp = requests.post("http://127.0.0.1:8000/detect", json={
                    "latitude": 26.7271,
                    "longitude": 88.3953,
                    "confidence": max(0.50, round(best_conf, 2)),
                    "elephant_count": count,
                    "source": "drone_live_cam"
                }, timeout=1)
                
                if resp.status_code == 200:
                    data = resp.json()
                    # Trigger Email Alert
                    send_elephant_email_alert(
                        detection_id=data.get("id", 1),
                        count=count,
                        confidence=best_conf,
                        lat=26.7271,
                        lon=88.3953
                    )
                last_auto_alert = now
            except Exception:
                pass

        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(generate_annotated_feed(), media_type="multipart/x-mixed-replace; boundary=frame")
