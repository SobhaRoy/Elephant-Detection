import requests

BASE_URL = "http://127.0.0.1:8000"

def run_contract_tests():
    print("=== EleGuard AI: API Contract v1.0 Test Suite ===\n")

    # 1. Health Check
    r = requests.get(f"{BASE_URL}/")
    assert r.status_code == 200 and r.json().get("version") == "1.0", "GET / failed"
    print("[PASS] GET / (Health Check)")

    # 2. System Status
    r = requests.get(f"{BASE_URL}/status")
    assert r.status_code == 200 and r.json().get("database") == "connected", "GET /status failed"
    print("[PASS] GET /status (System Status)")

    # 3. Validation: Reject confidence below 0.50
    invalid_payload = {
        "latitude": 26.7271, "longitude": 88.3953,
        "confidence": 0.42, "elephant_count": 1, "source": "drone_01"
    }
    r = requests.post(f"{BASE_URL}/detect", json=invalid_payload)
    assert r.status_code == 422, "Failed: Confidence < 0.50 was not rejected"
    print("[PASS] Validation: Confidence < 0.50 correctly rejected (HTTP 422)")

    # 4. Valid Detection
    valid_payload = {
        "latitude": 26.7271, "longitude": 88.3953,
        "confidence": 0.94, "elephant_count": 2, "source": "drone_01"
    }
    r = requests.post(f"{BASE_URL}/detect", json=valid_payload)
    assert r.status_code == 200 and r.json().get("alert") is True, "POST /detect failed"
    print("[PASS] POST /detect (Valid elephant detection stored)")

    # 5. Detection History
    r = requests.get(f"{BASE_URL}/detections")
    assert r.status_code == 200 and isinstance(r.json(), list), "GET /detections failed"
    print(f"[PASS] GET /detections (Retrieved {len(r.json())} incident records)")

    # 6. Latest Detection
    r = requests.get(f"{BASE_URL}/latest")
    assert r.status_code == 200 and r.json().get("alert") is True, "GET /latest failed"
    print("[PASS] GET /latest (Retrieved latest telemetry packet)")

    # 7. Manual Alert Trigger
    r = requests.post(f"{BASE_URL}/alert", json={"level": "HIGH", "message": "Manual test alert"})
    assert r.status_code == 200 and r.json().get("flash") is True, "POST /alert failed"
    print("[PASS] POST /alert (Flash alert triggered)")

    print("\nAll endpoints and validation rules adhere strictly to API Contract v1.0!")

if __name__ == "__main__":
    run_contract_tests()
