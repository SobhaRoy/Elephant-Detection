import time
import requests
import random
from datetime import datetime, timezone

BASE_URL = "http://127.0.0.1:8000"

# Realistic coordinates around Mahananda / Dooars forest fringe corridor
SIMULATED_WAYPOINTS = [
    {"lat": 26.7271, "lon": 88.3953, "count": 2, "source": "drone_alpha"},
    {"lat": 26.7310, "lon": 88.4010, "count": 3, "source": "drone_alpha"},
    {"lat": 26.7155, "lon": 88.3821, "count": 1, "source": "drone_beta"},
    {"lat": 26.7402, "lon": 88.4150, "count": 4, "source": "drone_alpha"},
]

def run_simulation(cycles=5):
    print("=== Starting Drone Ingestion Simulation ===")
    for i in range(cycles):
        point = random.choice(SIMULATED_WAYPOINTS)
        confidence = round(random.uniform(0.65, 0.98), 2)
        
        payload = {
            "latitude": point["lat"],
            "longitude": point["lon"],
            "confidence": confidence,
            "elephant_count": point["count"],
            "source": point["source"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # 1. Post simulated detection
            res = requests.post(f"{BASE_URL}/detect", json=payload)
            print(f"[Cycle {i+1}] Sent: {point['count']} elephants @ ({point['lat']}, {point['lon']}) | Status: {res.status_code}")
            
            # 2. Query latest endpoint
            latest = requests.get(f"{BASE_URL}/latest").json()
            print(f"       -> Confirmed Latest ID: {latest.get('id')} | Active Alert: {latest.get('alert')}")
            
        except Exception as e:
            print(f"Error connecting to server: {e}")
            
        time.sleep(3)
    print("=== Simulation Complete ===")

if __name__ == "__main__":
    run_simulation()
