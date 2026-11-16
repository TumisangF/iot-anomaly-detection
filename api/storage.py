import sqlite3
from contextlib import closing
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "predictions.db"


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(DB_PATH)) as connection, connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY,
                sensor_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                temperature_c REAL NOT NULL,
                humidity_pct REAL NOT NULL,
                sound_db REAL NOT NULL,
                anomaly_score REAL NOT NULL,
                threshold REAL NOT NULL,
                is_anomaly INTEGER NOT NULL
            )
        """)

def save_predictions(pairs):
    rows = [
        (
            reading.sensor_id,
            reading.timestamp.isoformat(),
            reading.temperature_c,
            reading.humidity_pct,
            reading.sound_db,
            prediction.anomaly_score,
            prediction.threshold,
            int(prediction.is_anomaly),
        )
        for reading, prediction in pairs
    ]

    with closing(sqlite3.connect(DB_PATH)) as connection, connection:
        connection.executemany(
            """
            INSERT INTO predictions (
                sensor_id, timestamp, temperature_c, humidity_pct, sound_db,
                anomaly_score, threshold, is_anomaly
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )