"""
AI Service — nạp model.joblib khi khởi động, expose /predict, /health, /model-info, /schema.
Hỗ trợ cả model có nhãn dạng số (0/1) lẫn nhãn dạng chữ (B/M).
"""

import json
from pathlib import Path
from typing import Dict

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Breast Cancer AI Service")

MODEL_DIR = Path(__file__).parent.parent / "models"
MODEL_PATH = MODEL_DIR / "model.joblib"
SCHEMA_PATH = MODEL_DIR / "schema.json"
METADATA_PATH = MODEL_DIR / "metadata.json"

model = None
schema = None
metadata = None
malignant_index = None  # vị trí lớp "ác tính" trong model.classes_


def _malignant_label(classes):
    """Xác định nhãn nào là 'ác tính' dù model dùng nhãn số (1) hay chữ (M)."""
    classes = list(classes)
    for candidate in ("M", 1, "1", "malignant"):
        if candidate in classes:
            return candidate
    return classes[-1]  # fallback: giả định lớp cuối là positive class


@app.on_event("startup")
def load_model():
    global model, schema, metadata, malignant_index
    model = joblib.load(MODEL_PATH)
    schema = json.loads(SCHEMA_PATH.read_text())
    metadata = json.loads(METADATA_PATH.read_text())
    positive_label = _malignant_label(model.classes_)
    malignant_index = list(model.classes_).index(positive_label)
    print(f"Model '{metadata['model_name']}' loaded — {len(schema['features'])} features expected. "
          f"classes_={list(model.classes_)}, malignant_index={malignant_index}")


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}


@app.get("/model-info")
def model_info():
    if metadata is None:
        raise HTTPException(status_code=503, detail="Model chưa được nạp")
    return metadata


@app.get("/schema")
def get_schema():
    if schema is None:
        raise HTTPException(status_code=503, detail="Schema chưa được nạp")
    return schema


class PredictRequest(BaseModel):
    features: Dict[str, float]


@app.post("/predict")
def predict(payload: PredictRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model chưa được nạp")

    expected = schema["features"]
    missing = [f for f in expected if f not in payload.features]
    unknown = [f for f in payload.features if f not in expected]
    if missing:
        raise HTTPException(status_code=422, detail={"error": "Thiếu đặc trưng", "missing": missing})
    if unknown:
        raise HTTPException(status_code=422, detail={"error": "Đặc trưng không xác định", "unknown": unknown})

    row = pd.DataFrame([[payload.features[f] for f in expected]], columns=expected)
    raw_pred = model.predict(row)[0]
    proba = float(model.predict_proba(row)[0, malignant_index])
    is_malignant = raw_pred == model.classes_[malignant_index]

    return {
        "diagnosis": "M" if is_malignant else "B",
        "diagnosis_label": "Ác tính (Malignant)" if is_malignant else "Lành tính (Benign)",
        "probability_malignant": round(proba, 4),
        "model_used": metadata["model_name"],
    }
