# IoT Anomaly Detection as a Service

Task 1 for DLBDSMTP01. The project will use simulated temperature,
humidity, and sound readings to detect unusual patterns in
wind-turbine component production.

## Current status

Phase 0 sets up the repository and Python environment. Phase 1 will
define the architecture and the data passed between components.

## Local setup

Run these commands from the repository root in Git Bash on Windows:

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
```

## Planned project structure

- `simulator/` — Generate training data and stream sensor readings.
- `data/` — Store generated datasets locally.
- `model/` — Train and evaluate the anomaly detector.
- `api/` — Serve anomaly scores through FastAPI.
- `monitoring/` — Track service metrics and prediction scores.
- `docs/` — Keep architecture diagrams and design notes.
- `tests/` — Verify the simulator, model, and API.
