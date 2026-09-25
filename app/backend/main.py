"""
Backend — validate input theo schema từ AI Service, gọi AI Service, lưu lịch sử.
Nếu MONGO_URI được cấu hình -> lưu MongoDB Atlas; nếu không -> lưu tạm trong bộ nhớ (dev/test).
"""

import os
from datetime import datetime
from typing import Dict

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Breast Cancer Backend")

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8000")
MONGO_URI = os.getenv("MONGO_URI", "")

_mongo_collection = None
_memory_history = []  # fallback khi chưa cấu hình MongoDB

if MONGO_URI:
    from pymongo import MongoClient
    _client = MongoClient(MONGO_URI)
    _mongo_collection = _client.get_default_database()["predictions"]


def save_history(record: dict):
    if _mongo_collection is not None:
        _mongo_collection.insert_one(record)
    else:
        _memory_history.append(record)
        if len(_memory_history) > 100:
            _memory_history.pop(0)


@app.get("/health")
def health():
    return {"status": "ok", "storage": "mongodb" if _mongo_collection is not None else "memory"}


@app.get("/api/schema")
async def get_schema():
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{AI_SERVICE_URL}/schema", timeout=10)
        resp.raise_for_status()
        return resp.json()


class PredictRequest(BaseModel):
    features: Dict[str, float]


@app.post("/api/predict")
async def predict(payload: PredictRequest):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{AI_SERVICE_URL}/predict", json=payload.model_dump(), timeout=10
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json())
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"AI Service lỗi: {exc}")

    result = resp.json()
    save_history({
        "features": payload.features,
        "result": result,
        "timestamp": datetime.utcnow().isoformat(),
    })
    return result


@app.get("/api/history")
def history():
    if _mongo_collection is not None:
        items = list(_mongo_collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(50))
    else:
        items = list(reversed(_memory_history))
    return {"items": items, "storage": "mongodb" if _mongo_collection is not None else "memory"}
