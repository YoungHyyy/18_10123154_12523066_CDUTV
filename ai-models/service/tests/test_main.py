import json
from pathlib import Path

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "models" / "schema.json"
with SCHEMA_PATH.open(encoding="utf-8") as schema_file:
    schema = json.load(schema_file)


def valid_features():
    return {
        feature["name"]: (feature["min"] + feature["max"]) / 2
        for feature in schema["features"]
    }


def test_health_reports_service_status():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "ai-service"
    assert response.json()["port"] == 8001


def test_model_info_reports_loaded_model():
    response = client.get("/model-info")

    assert response.status_code == 200
    assert response.json()["model_version"]
    assert response.json()["metrics"]


def test_predict_accepts_valid_features():
    response = client.post("/predict", json={"features": valid_features()})

    assert response.status_code == 200
    assert response.json()["prediction"] in {"benign", "malignant"}
    assert 0 <= response.json()["probability"] <= 1


def test_predict_rejects_missing_feature():
    features = valid_features()
    features.pop(next(iter(features)))

    response = client.post("/predict", json={"features": features})

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_input"


def test_predict_rejects_invalid_request_shape():
    response = client.post("/predict", json={"features": "not-an-object"})

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_input"


def test_predict_rejects_extra_feature():
    features = valid_features()
    features["unexpected"] = 1.0

    response = client.post("/predict", json={"features": features})

    assert response.status_code == 400
    assert "Thừa cột" in response.json()["detail"]


def test_predict_rejects_out_of_range_feature():
    features = valid_features()
    feature = schema["features"][0]
    features[feature["name"]] = feature["max"] + 1

    response = client.post("/predict", json={"features": features})

    assert response.status_code == 400
    assert "ngoài khoảng" in response.json()["detail"]
