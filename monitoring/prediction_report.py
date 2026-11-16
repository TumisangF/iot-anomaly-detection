import argparse
import sqlite3
from contextlib import closing
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Summarize stored predictions")
    parser.add_argument("--db", type=Path, default=Path("data/predictions.db"))
    args = parser.parse_args()

    if not args.db.is_file():
        parser.exit(1, f"Prediction database not found: {args.db}\n")

    db_uri = f"{args.db.resolve().as_uri()}?mode=ro"
    with closing(sqlite3.connect(db_uri, uri=True)) as db:
        count, flagged, low, mean, high = db.execute("""
            SELECT COUNT(*), COALESCE(SUM(is_anomaly), 0),
                   MIN(anomaly_score), AVG(anomaly_score), MAX(anomaly_score)
            FROM predictions
        """).fetchone()

        recent = db.execute("""
            SELECT timestamp, sensor_id, anomaly_score, threshold, is_anomaly
            FROM predictions
            ORDER BY id DESC
            LIMIT 5
        """).fetchall()

    print(f"Predictions stored: {count}")
    if count == 0:
        print("Send a reading to /predict to populate the report.")
        return

    print(f"Flagged readings: {flagged} ({flagged / count:.1%})")
    print(f"Score range: {low:.4f} to {high:.4f} (mean {mean:.4f})")
    print("\nLatest predictions")
    for timestamp, sensor_id, score, threshold, is_anomaly in recent:
        label = "FLAGGED" if is_anomaly else "NORMAL"
        print(f"{timestamp}  {sensor_id}  {score:.4f} / {threshold:.4f}  {label}")


if __name__ == "__main__":
    main()
