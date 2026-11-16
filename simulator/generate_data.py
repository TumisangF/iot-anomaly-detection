import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

FIELDNAMES = (
    "sensor_id",
    "timestamp",
    "temperature_c",
    "humidity_pct",
    "sound_db",
)
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "normal_train.csv"


def normal_reading(rng, timestamp, sensor_id="line-01"):
    load = rng.gauss(0, 1)
    temperature = 26 + 0.8 * load + rng.gauss(0, 0.6)
    humidity = 48 - 1.2 * load + rng.gauss(0, 1.5)
    sound = 68 + 1.5 * load + rng.gauss(0, 1.0)

    return {
        "sensor_id": sensor_id,
        "timestamp": timestamp.isoformat(),
        "temperature_c": round(temperature, 2),
        "humidity_pct": round(humidity, 2),
        "sound_db": round(sound, 2),
    }


def main():
    rng = random.Random(42)
    start = datetime(2026, 11, 16, 20, 0, tzinfo=timezone.utc)
    row_count = 2000

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        for second in range(row_count):
            timestamp = start + timedelta(seconds=second)
            writer.writerow(normal_reading(rng, timestamp))

    print(f"Wrote {row_count} readings to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()