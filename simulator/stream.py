import argparse
import csv
import json
import time
from datetime import datetime, timezone

import requests

from simulator.generate_data import OUTPUT_PATH

TEST_DATA = OUTPUT_PATH.parent / "test.csv"


def main():
    parser = argparse.ArgumentParser(description="Replay simulated sensor data")
    parser.add_argument("--url", default="http://127.0.0.1:8000/predict")
    parser.add_argument("--limit", type=int, help="Maximum readings to replay")
    parser.add_argument("--dry-run", action="store_true", help="Print JSON locally")
    args = parser.parse_args()

    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")

    if not TEST_DATA.is_file():
        parser.exit(1, "Run python -m simulator.generate_evaluation_data first.\n")

    with TEST_DATA.open(newline="", encoding="utf-8") as file:
        for index, row in enumerate(csv.DictReader(file)):
            if args.limit is not None and index >= args.limit:
                break
            if index:
                time.sleep(1)

            reading = {
                "sensor_id": row["sensor_id"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "temperature_c": float(row["temperature_c"]),
                "humidity_pct": float(row["humidity_pct"]),
                "sound_db": float(row["sound_db"]),
            }

            if args.dry_run:
                print(json.dumps(reading), flush=True)
                continue

            try:
                response = requests.post(args.url, json=reading, timeout=5)
                response.raise_for_status()
            except requests.RequestException as error:
                parser.exit(1, f"Reading {index + 1} failed: {error}\n")

            print(response.text, flush=True)


if __name__ == "__main__":
    main()