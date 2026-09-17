from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .database import get_db
from .models import DetectionRecord, DetectionCreate, AlertRequest

router = APIRouter()

latest_alert_state = {
    "flash": False,
    "level": "NORMAL",
    "message": "System monitoring active"
}

@router.get("/")
def health_check():
    return {"message": "EleGuard AI Backend Running", "version": "1.0"}

@router.post("/detect")
def save_detection(payload: DetectionCreate, db: Session = Depends(get_db)):
    ts = payload.timestamp if payload.timestamp else datetime.now(timezone.utc)
    
    record = DetectionRecord(
        timestamp=ts,
        latitude=payload.latitude,
        longitude=payload.longitude,
        confidence=payload.confidence,
        elephant_count=payload.elephant_count,
        source=payload.source
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    latest_alert_state["flash"] = True
    latest_alert_state["level"] = "HIGH"
    latest_alert_state["message"] = f"Elephant herd of {payload.elephant_count} spotted!"

    return {
        "status": "success",
        "alert": True,
        "message": "Elephant detected and stored.",
        "id": record.id
    }

@router.get("/detections")
def get_detections(db: Session = Depends(get_db)):
    records = db.query(DetectionRecord).order_by(desc(DetectionRecord.timestamp)).limit(50).all()
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat() if hasattr(r.timestamp, "isoformat") else str(r.timestamp),
            "latitude": r.latitude,
            "longitude": r.longitude,
            "confidence": r.confidence,
            "elephant_count": r.elephant_count,
            "source": r.source
        }
        for r in records
    ]

@router.get("/latest")
def get_latest_detection(db: Session = Depends(get_db)):
    r = db.query(DetectionRecord).order_by(desc(DetectionRecord.timestamp)).first()
    if not r:
        return {"id": None, "confidence": 0.0, "alert": False, "flash": False}
    
    should_flash = latest_alert_state["flash"]
    latest_alert_state["flash"] = False
    
    return {
        "id": r.id,
        "confidence": r.confidence,
        "elephant_count": r.elephant_count,
        "latitude": r.latitude,
        "longitude": r.longitude,
        "source": r.source,
        "timestamp": r.timestamp.isoformat() if hasattr(r.timestamp, "isoformat") else str(r.timestamp),
        "alert": True,
        "flash": should_flash
    }

@router.post("/alert")
def trigger_alert(payload: AlertRequest):
    latest_alert_state["flash"] = True
    latest_alert_state["level"] = payload.level
    latest_alert_state["message"] = payload.message
    return {"status": "alert_sent", "flash": True}

@router.get("/status")
def system_status():
    return {
        "backend": "online",
        "database": "connected",
        "model": "loaded",
        "camera": "active"
    }
