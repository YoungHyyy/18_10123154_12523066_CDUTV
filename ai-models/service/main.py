"""AI Service - nạp model.joblib khi khởi động, phục vụ /predict."""
import json
import logging
import math
import os
import time
import uuid
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s ai-service %(message)s")
log = logging.getLogger("ai-service")

MODELS_DIR = Path(os.getenv("MODELS_DIR", Path(__file__).resolve().parents[1] / "models"))
SERVICE_PORT = int(os.getenv("PORT", "8001"))
START_TIME = time.time()

app = FastAPI(title="Breast Cancer AI Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",")],
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
    model_config = ConfigDict(extra="forbid")

    features: dict[str, float] = Field(min_length=1)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "error": "invalid_input",
            "detail": "Dữ liệu yêu cầu không hợp lệ",
        },
    )


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
    return {
        "status": "ok",
        "service": "ai-service",
        "port": SERVICE_PORT,
        "uptime_seconds": round(time.time() - START_TIME, 1),
    }


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
    extra = [c for c in req.features if c not in FEATURE_NAMES]
    if missing:
        return JSONResponse(status_code=400, content={
            "error": "invalid_input",
            "detail": f"Thiếu cột: {', '.join(missing)}",
        })
    if extra:
        return JSONResponse(status_code=400, content={
            "error": "invalid_input",
            "detail": f"Thừa cột: {', '.join(extra)}",
        })

    invalid = []
    for feature in SCHEMA["features"]:
        name = feature["name"]
        value = req.features[name]
        if not math.isfinite(value) or value < feature["min"] or value > feature["max"]:
            invalid.append(name)
    if invalid:
        return JSONResponse(status_code=400, content={
            "error": "invalid_input",
            "detail": f"Giá trị ngoài khoảng hợp lệ hoặc không hữu hạn: {', '.join(invalid)}",
        })

    row = pd.DataFrame([{c: req.features[c] for c in FEATURE_NAMES}])
    pred = int(MODEL.predict(row)[0])
    proba = float(MODEL.predict_proba(row)[0, 1])

    return {
        "prediction": SCHEMA["labels"][str(pred)],
        "probability": round(proba, 4),
        "model_version": METADATA["model_version"],
    }