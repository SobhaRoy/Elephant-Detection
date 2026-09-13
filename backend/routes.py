import csv
import io
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from .database import get_db
from .models import (
    DetectionRecord,
    DetectionCreate,
    DetectionResponse,
    AlertRequest,
    AlertResponse
)

router = APIRouter()

# ------------------------------------------------------------------
# WebSocket Connection Manager for Real-Time Dashboard Broadcasting
# ------------------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                pass

manager = ConnectionManager()

system_alert_state = {
    "active": False,
    "last_level": "NORMAL",
    "last_message": "Monitoring active"
}

CORRIDOR_ZONES = [
    {"name": "Sevoke-Gulma Rail Corridor", "min_lat": 26.710, "max_lat": 26.745, "min_lon": 88.380, "max_lon": 88.420}
]

def evaluate_risk(lat: float, lon: float, count: int) -> str:
    for zone in CORRIDOR_ZONES:
        if zone["min_lat"] <= lat <= zone["max_lat"] and zone["min_lon"] <= lon <= zone["max_lon"]:
            return "CRITICAL_RAIL_CORRIDOR"
    if count >= 3:
        return "HIGH_HERD_RISK"
    return "STANDARD_MONITORING"

@router.get("/", summary="Health Check")
def health_check() -> Dict[str, str]:
    return {
        "message": "EleGuard AI Backend Running",
        "version": "1.2"
    }

@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """Real-time push channel for Member 3's dashboard flash alerts."""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.post("/detect", summary="Ingest Elephant Detection")
async def ingest_detection(payload: DetectionCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    if payload.confidence < 0.50:
        return {
            "status": "ignored",
            "alert": False,
            "message": f"Confidence {payload.confidence:.2f} is below the 0.50 operational threshold."
        }

    risk_zone = evaluate_risk(payload.latitude, payload.longitude, payload.elephant_count)

    record = DetectionRecord(
        timestamp=payload.timestamp,
        latitude=payload.latitude,
        longitude=payload.longitude,
        confidence=payload.confidence,
        elephant_count=payload.elephant_count,
        source=payload.source or "drone_01"
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    system_alert_state["active"] = True
    system_alert_state["last_level"] = "HIGH" if risk_zone != "STANDARD_MONITORING" else "MEDIUM"
    system_alert_state["last_message"] = (
        f"[{risk_zone}] {payload.elephant_count} elephant(s) detected ({payload.confidence*100:.1f}% confidence)."
    )

    alert_packet = {
        "event": "ELEPHANT_DETECTED",
        "id": record.id,
        "latitude": record.latitude,
        "longitude": record.longitude,
        "count": record.elephant_count,
        "confidence": record.confidence,
        "risk_level": risk_zone,
        "timestamp": record.timestamp.isoformat()
    }
    # Instant push to all connected browser dashboards
    await manager.broadcast(alert_packet)

    return {
        "status": "success",
        "alert": True,
        "risk_level": risk_zone,
        "message": "Elephant detected and stored.",
        "detection_id": record.id
    }

@router.get("/detections", response_model=List[DetectionResponse], summary="Detection History")
def get_detections(limit: int = 50, db: Session = Depends(get_db)):
    records = db.query(DetectionRecord).order_by(desc(DetectionRecord.timestamp)).limit(limit).all()
    return records

@router.get("/latest", summary="Get Latest Sighting")
def get_latest(db: Session = Depends(get_db)) -> Dict[str, Any]:
    latest_record = db.query(DetectionRecord).order_by(desc(DetectionRecord.timestamp)).first()
    if not latest_record:
        return {
            "id": None,
            "confidence": 0.0,
            "alert": False,
            "message": "No sightings recorded yet."
        }
    return {
        "id": latest_record.id,
        "timestamp": latest_record.timestamp.isoformat(),
        "latitude": latest_record.latitude,
        "longitude": latest_record.longitude,
        "confidence": latest_record.confidence,
        "elephant_count": latest_record.elephant_count,
        "source": latest_record.source,
        "alert": True
    }

@router.post("/alert", response_model=AlertResponse, summary="Manual Alert Trigger")
async def trigger_alert(alert_in: AlertRequest):
    system_alert_state["active"] = True
    system_alert_state["last_level"] = alert_in.level
    system_alert_state["last_message"] = alert_in.message
    await manager.broadcast({"event": "MANUAL_ALERT", "level": alert_in.level, "message": alert_in.message})
    return AlertResponse(status="alert_sent", flash=True)

@router.get("/status", summary="System Health & Alert State")
def get_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    db_status = "connected"
    try:
        db.execute(DetectionRecord.__table__.select().limit(1))
    except Exception:
        db_status = "disconnected"

    return {
        "backend": "online",
        "database": db_status,
        "model": "loaded",
        "camera": "active",
        "alert_active": system_alert_state["active"],
        "alert_message": system_alert_state["last_message"]
    }

@router.get("/analytics/summary", summary="Corridor Risk Analytics")
def get_analytics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    total_sightings = db.query(func.count(DetectionRecord.id)).scalar() or 0
    total_elephants = db.query(func.sum(DetectionRecord.elephant_count)).scalar() or 0
    avg_conf = db.query(func.avg(DetectionRecord.confidence)).scalar() or 0.0
    max_herd = db.query(func.max(DetectionRecord.elephant_count)).scalar() or 0

    return {
        "total_detections": total_sightings,
        "total_elephants_logged": total_elephants,
        "average_confidence": round(float(avg_conf), 3),
        "peak_herd_size": max_herd
    }

@router.get("/map/geojson", summary="GeoJSON Feeds for Map Dashboard")
def get_geojson(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Provides GIS-standard GeoJSON points for Leaflet/OpenStreetMap UI integration."""
    records = db.query(DetectionRecord).all()
    features = []
    for r in records:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [r.longitude, r.latitude]
            },
            "properties": {
                "id": r.id,
                "confidence": r.confidence,
                "elephant_count": r.elephant_count,
                "source": r.source,
                "timestamp": r.timestamp.isoformat()
            }
        })
    return {
        "type": "FeatureCollection",
        "features": features
    }

@router.get("/export/csv", summary="Export Detections to CSV")
def export_detections_csv(db: Session = Depends(get_db)):
    records = db.query(DetectionRecord).order_by(desc(DetectionRecord.timestamp)).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Timestamp (UTC)", "Latitude", "Longitude", "Confidence", "Elephant Count", "Source Unit"])
    for r in records:
        writer.writerow([
            r.id,
            r.timestamp.isoformat() if r.timestamp else "",
            r.latitude,
            r.longitude,
            f"{r.confidence:.2f}",
            r.elephant_count,
            r.source
        ])
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=elephant_surveillance_report.csv"}
    )
