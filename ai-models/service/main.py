"""AI Service - nạp model.joblib khi khởi động, phục vụ /predict."""
import json
import logging
import time
import uuid
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s ai-service %(message)s")
log = logging.getLogger("ai-service")

MODELS_DIR = Path(__file__).resolve().parents[1] / "models"
START_TIME = time.time()

app = FastAPI(title="Breast Cancer AI Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # xem ghi chú CORS ở dưới
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Nạp model NGAY khi module được import (tức lúc container khởi động) ----
log.info("Đang nạp model...")
MODEL = joblib.load(MODELS_DIR / "model.joblib")
with open(MODELS_DIR / "schema.json", encoding="utf-8") as f:
    SCHEMA = json.load(f)
with open(MODELS_DIR / "metadata.json", encoding="utf-8") as f:
    METADATA = json.load(f)
FEATURE_NAMES = [f["name"] for f in SCHEMA["features"]]
log.info(f"Đã nạp model {METADATA['model_name']} (v{METADATA['model_version']}), {len(FEATURE_NAMES)} đặc trưng")


class PredictRequest(BaseModel):
    features: dict[str, float]


@app.middleware("http")
async def log_requests(request: Request, call_next):
    req_id = request.headers.get("x-request-id", uuid.uuid4().hex[:6])
    t0 = time.perf_counter()
    response = await call_next(request)
    ms = round((time.perf_counter() - t0) * 1000, 1)
    log.info(f"req={req_id} {request.method} {request.url.path} -> {response.status_code} in {ms}ms")
    response.headers["x-request-id"] = req_id
    return response


@app.get("/health")
def health():
    return {"status": "ok", "uptime_seconds": round(time.time() - START_TIME, 1)}


@app.get("/model-info")
def model_info():
    return {
        "model_name": METADATA["model_name"],
        "model_version": METADATA["model_version"],
        "metrics": METADATA["metrics_at_selection"],
        "trained_on": METADATA["trained_on"],
    }


@app.post("/predict")
def predict(req: PredictRequest):
    missing = [c for c in FEATURE_NAMES if c not in req.features]
    if missing:
        return JSONResponse(status_code=400, content={
            "error": "invalid_input",
            "detail": f"Thiếu cột: {', '.join(missing)}",
        })

    row = pd.DataFrame([{c: req.features[c] for c in FEATURE_NAMES}])
    pred = int(MODEL.predict(row)[0])
    proba = float(MODEL.predict_proba(row)[0, 1])

    return {
        "prediction": SCHEMA["labels"][str(pred)],
        "probability": round(proba, 4),
        "model_version": METADATA["model_version"],
    }