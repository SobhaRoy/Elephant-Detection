from datetime import datetime, timedelta, timezone
import random
from backend.database import SessionLocal, engine, Base
from backend.models import DetectionRecord

Base.metadata.create_all(bind=engine)
db = SessionLocal()

LOCATIONS = [
    {"lat": 26.7271, "lon": 88.3953, "source": "drone_sukna_01"},
    {"lat": 26.7410, "lon": 88.4110, "source": "drone_gulma_02"},
    {"lat": 26.7180, "lon": 88.3750, "source": "drone_sevoke_01"},
    {"lat": 26.7550, "lon": 88.4290, "source": "drone_dooars_03"}
]

def seed_database(num_records=10):
    print("Clearing old records...")
    db.query(DetectionRecord).delete()
    db.commit()

    print(f"Seeding {num_records} demonstration records...")
    now = datetime.now(timezone.utc)

    for i in range(num_records):
        loc = random.choice(LOCATIONS)
        record = DetectionRecord(
            timestamp=now - timedelta(minutes=(num_records - i) * 12),
            latitude=loc["lat"] + random.uniform(-0.002, 0.002),
            longitude=loc["lon"] + random.uniform(-0.002, 0.002),
            confidence=round(random.uniform(0.72, 0.98), 2),
            elephant_count=random.randint(1, 5),
            source=loc["source"]
        )
        db.add(record)

    db.commit()
    print("Database successfully seeded with realistic corridor detections!")
    db.close()

if __name__ == "__main__":
    seed_database()
