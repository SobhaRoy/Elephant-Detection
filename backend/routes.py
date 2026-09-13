from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .database import get_db
from .models import (
    DetectionRecord,
    DetectionCreate,
    DetectionResponse,
    AlertRequest,
    AlertResponse
)

router = APIRouter()

system_alert_state = {
    "active": False,
    "last_level": "NORMAL",
    "last_message": "Monitoring active"
}

@router.get("/", summary="Health Check")
def health_check() -> Dict[str, str]:
    return {
        "message": "EleGuard AI Backend Running",
        "version": "1.0"
    }

@router.post("/detect", summary="Ingest Elephant Detection")
def ingest_detection(payload: DetectionCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    if payload.confidence < 0.50:
        return {
            "status": "ignored",
            "alert": False,
            "message": f"Confidence {payload.confidence:.2f} is below the 0.50 operational threshold."
        }

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
    system_alert_state["last_level"] = "HIGH"
    system_alert_state["last_message"] = (
        f"{payload.elephant_count} elephant(s) detected with {payload.confidence*100:.1f}% confidence."
    )

    return {
        "status": "success",
        "alert": True,
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
def trigger_alert(alert_in: AlertRequest):
    system_alert_state["active"] = True
    system_alert_state["last_level"] = alert_in.level
    system_alert_state["last_message"] = alert_in.message
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
