from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200

def test_analyze_mock():
    r = client.post("/analyze", json={
        "idea": "Test idea",
        "objective": "Test objective",
        "constraints": {"time": "1 week"},
        "success_criteria": ["works"],
        "context": {"stage": "test"},
        "hat_sequence": ["WHITE","BLUE"]
    })
    assert r.status_code == 200
    data = r.json()
    assert "state" in data
    assert data["final_hat"] == "BLUE"
