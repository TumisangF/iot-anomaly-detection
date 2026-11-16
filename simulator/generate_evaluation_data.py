import csv
import random
from collections import Counter
from datetime import datetime, timedelta, timezone

from simulator.generate_data import FIELDNAMES, OUTPUT_PATH, normal_reading

EVALUATION_FIELDS = (*FIELDNAMES, "is_anomaly", "anomaly_type")


def generate_dataset(filename, seed, start):
    rng = random.Random(seed)
    path = OUTPUT_PATH.parent / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter()

    # Sample one event start from each of three non-overlapping windows.
    spike_at = rng.randrange(100, 250)
    drift_at = rng.randrange(350, 550)
    shift_at = rng.randrange(700, 850)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=EVALUATION_FIELDS)
        writer.writeheader()

        for second in range(1000):
            row = normal_reading(rng, start + timedelta(seconds=second))
            anomaly_type = "normal"

            if spike_at <= second < spike_at + 5:
                row["sound_db"] = round(row["sound_db"] + 20, 2)
                anomaly_type = "sound_spike"
            elif drift_at <= second < drift_at + 30:
                increase = 0.25 * (second - drift_at + 1)
                row["temperature_c"] = round(row["temperature_c"] + increase, 2)
                anomaly_type = "temperature_drift"
            elif shift_at <= second < shift_at + 20:
                row["temperature_c"] = round(row["temperature_c"] + 4, 2)
                row["humidity_pct"] = round(row["humidity_pct"] + 6, 2)
                row["sound_db"] = round(row["sound_db"] + 5, 2)
                anomaly_type = "combined_shift"

            row["is_anomaly"] = int(anomaly_type != "normal")
            row["anomaly_type"] = anomaly_type
            writer.writerow(row)
            counts[anomaly_type] += 1

    print(f"{path.name}: {dict(counts)}")


if __name__ == "__main__":
    start = datetime(2026, 11, 17, 8, 0, tzinfo=timezone.utc)
    generate_dataset("validation.csv", seed=101, start=start)
    generate_dataset("test.csv", seed=202, start=start + timedelta(hours=1))