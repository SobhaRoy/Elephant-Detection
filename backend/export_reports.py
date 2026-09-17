import os
import sys
import csv
from datetime import datetime

# Ensure the root project directory is on the import path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import DetectionRecord

DB_PATH = os.path.join(BASE_DIR, "database", "detections.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def export_audit_report():
    session = SessionLocal()
    try:
        records = session.query(DetectionRecord).order_by(DetectionRecord.timestamp.desc()).all()
        
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        reports_dir = os.path.join(BASE_DIR, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        csv_file = os.path.join(reports_dir, f"incident_report_{timestamp_str}.csv")
        
        with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Incident ID", "Timestamp (UTC)", "Latitude", "Longitude", "Confidence Score", "Herd Count", "Telemetry Source"])
            for r in records:
                ts = r.timestamp.isoformat() if hasattr(r.timestamp, "isoformat") else str(r.timestamp)
                writer.writerow([r.id, ts, r.latitude, r.longitude, f"{r.confidence:.2f}", r.elephant_count, r.source])
                
        print(f"[SUCCESS] Exported {len(records)} records to {csv_file}")
    except Exception as e:
        print(f"[ERROR] Failed to export report: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    export_audit_report()
