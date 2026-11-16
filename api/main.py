from contextlib import asynccontextmanager
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, Request
from pydantic import AwareDatetime, BaseModel, Field, FiniteFloat

import logging
import sqlite3

from fastapi import FastAPI, HTTPException, Request

from api.storage import init_db, save_predictions
from time import perf_counter

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parents[1] / "model" / "isolation_forest.joblib"


class SensorReading(BaseModel):
    sensor_id: str = Field(min_length=1)
    timestamp: AwareDatetime
    temperature_c: FiniteFloat
    humidity_pct: FiniteFloat = Field(ge=0, le=100)
    sound_db: FiniteFloat

class PredictionBatch(BaseModel):
    readings: list[SensorReading] = Field(min_length=1, max_length=100)


class Prediction(BaseModel):
    sensor_id: str
    timestamp: AwareDatetime
    anomaly_score: float
    threshold: float
    is_anomaly: bool


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not MODEL_PATH.is_file():
        raise RuntimeError(
            f"Model artifact missing at {MODEL_PATH}. Run python -m model.train."
        )

    app.state.artifact = joblib.load(MODEL_PATH)
    init_db()
    yield


app = FastAPI(title="IoT Anomaly Detection", lifespan=lifespan)

request_logger = logging.getLogger("uvicorn.error")


@app.middleware("http")
async def log_request(request: Request, call_next):
    started_at = perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        elapsed_ms = (perf_counter() - started_at) * 1000
        request_logger.info(
            "%s %s status=%d duration_ms=%.1f",
            request.method,
            request.url.path,
            status_code,
            elapsed_ms,
        )


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": True}


def score_and_save(readings, artifact):
    features = artifact["features"]
    inputs = pd.DataFrame(
        [reading.model_dump() for reading in readings],
        columns=features,
    )
    scores = -artifact["model"].score_samples(inputs)
    threshold = float(artifact["threshold"])

    predictions = [
        Prediction(
            sensor_id=reading.sensor_id,
            timestamp=reading.timestamp,
            anomaly_score=float(score),
            threshold=threshold,
            is_anomaly=bool(score >= threshold),
        )
        for reading, score in zip(readings, scores)
    ]

    try:
        save_predictions(zip(readings, predictions))
    except sqlite3.Error:
        logger.exception("Could not save predictions")
        raise HTTPException(
            status_code=503, detail="Prediction storage is unavailable"
        ) from None

    return predictions


@app.post("/predict", response_model=Prediction)
def predict(reading: SensorReading, request: Request):
    return score_and_save([reading], request.app.state.artifact)[0]


@app.post("/predict/batch", response_model=list[Prediction])
def predict_batch(batch: PredictionBatch, request: Request):
    return score_and_save(batch.readings, request.app.state.artifact)