from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["message"] == "EleGuard AI Backend Running"

def test_low_confidence_dropped():
    payload = {
        "latitude": 26.7271,
        "longitude": 88.3953,
        "confidence": 0.35,
        "elephant_count": 1,
        "source": "drone_test"
    }
    res = client.post("/detect", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "ignored"
    assert res.json()["alert"] is False

def test_valid_detection_stored():
    payload = {
        "latitude": 26.7271,
        "longitude": 88.3953,
        "confidence": 0.88,
        "elephant_count": 2,
        "source": "drone_test"
    }
    res = client.post("/detect", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert res.json()["alert"] is True

def test_get_latest():
    res = client.get("/latest")
    assert res.status_code == 200
    data = res.json()
    assert "id" in data
    assert "latitude" in data

def test_get_status():
    res = client.get("/status")
    assert res.status_code == 200
    assert res.json()["backend"] == "online"
    assert res.json()["database"] == "connected"
