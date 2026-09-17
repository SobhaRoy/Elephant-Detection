from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, Float, String, DateTime
from pydantic import BaseModel, field_validator
from .database import Base

class DetectionRecord(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    elephant_count = Column(Integer, default=1, nullable=False)
    source = Column(String, default="drone_01", nullable=False)

class DetectionCreate(BaseModel):
    timestamp: Optional[datetime] = None
    latitude: float
    longitude: float
    confidence: float
    elephant_count: int = 1
    source: str = "drone_01"

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if v < 0.50:
            raise ValueError("Confidence below 0.50 is rejected per API Contract.")
        return round(float(v), 2)

    @field_validator("elephant_count")
    @classmethod
    def validate_count(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Elephant count must be at least 1.")
        return int(v)

class AlertRequest(BaseModel):
    level: str = "HIGH"
    message: str = "Elephant detected."
