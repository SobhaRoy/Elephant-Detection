from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, Integer, Float, String, DateTime
from pydantic import BaseModel, Field, field_validator
from .database import Base

class DetectionRecord(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    elephant_count = Column(Integer, nullable=False, default=1)
    source = Column(String(50), nullable=False, default="drone_01")

class DetectionCreate(BaseModel):
    latitude: float = Field(..., description="GPS Latitude coordinate")
    longitude: float = Field(..., description="GPS Longitude coordinate")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score (0.0 to 1.0)")
    elephant_count: int = Field(default=1, ge=1, description="Elephant count must be at least 1")
    source: Optional[str] = Field(default="drone_01", description="Identifier for drone or camera")
    timestamp: Optional[datetime] = Field(default=None, description="ISO timestamp; server time used if omitted")

    @field_validator("timestamp", mode="before")
    @classmethod
    def set_server_timestamp_if_missing(cls, v):
        if v is None or str(v).strip() == "":
            return datetime.now(timezone.utc)
        return v

class DetectionResponse(BaseModel):
    id: int
    timestamp: datetime
    latitude: float
    longitude: float
    confidence: float
    elephant_count: int
    source: str

    class Config:
        from_attributes = True

class AlertRequest(BaseModel):
    level: str = Field(default="HIGH", description="Alert severity level: LOW, MEDIUM, HIGH")
    message: str = Field(default="Elephant detected.", description="Alert description text")

class AlertResponse(BaseModel):
    status: str
    flash: bool
