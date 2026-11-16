import math
import re
import sys
from statistics import mean

REQUEST_LOG = re.compile(
    r"\bPOST /predict(?:/batch)? status=(\d{3}) duration_ms=(\d+(?:\.\d+)?)\b"
)


def main():
    statuses = []
    durations = []

    for line in sys.stdin:
        match = REQUEST_LOG.search(line)
        if match:
            statuses.append(int(match[1]))
            durations.append(float(match[2]))

    total = len(statuses)
    print(f"Prediction requests: {total}")
    if not total:
        print("No prediction request logs in the selected window.")
        return

    client_errors = sum(400 <= status < 500 for status in statuses)
    server_errors = sum(500 <= status < 600 for status in statuses)
    p95 = sorted(durations)[math.ceil(0.95 * total) - 1]

    print(f"Client errors (4xx): {client_errors} ({client_errors / total:.1%})")
    print(f"Server errors (5xx): {server_errors} ({server_errors / total:.1%})")
    print(f"Mean latency: {mean(durations):.1f} ms")
    print(f"95th-percentile latency: {p95:.1f} ms")


if __name__ == "__main__":
    main()
