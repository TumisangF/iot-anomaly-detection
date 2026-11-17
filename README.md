# IoT Anomaly Detection as a Service

A DLBDSMTP01 Task 1 project that detects unusual temperature, humidity,
and sound readings in simulated wind-turbine component production.

Simulator → FastAPI → Isolation Forest → SQLite → monitoring reports

The API scores individual readings or batches. It flags a reading when its
score meets or exceeds the threshold selected on validation data, then stores
the reading, score, threshold, and decision in SQLite.

## Reproduce the local Docker demo

You need Python 3.13 and Docker Desktop running in Linux container mode.
Run the commands from the repository root. The activation command below
is for Git Bash on Windows.

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt -r requirements-api.txt

python -m simulator.generate_data
python -m simulator.generate_evaluation_data
python -m model.train

docker build --build-arg PYTHON_VERSION=3.13 -t iot-anomaly-api:local .
```

The training command creates `model/isolation_forest.joblib` and logs the
evaluation to MLflow. Generated CSVs and model artifacts are recreated locally.

Start the API on port `8001` with a named volume for predictions:

```bash
MSYS_NO_PATHCONV=1 docker run -d --name iot-anomaly-api \
  -p 127.0.0.1:8001:8000 \
  --mount type=volume,source=iot-anomaly-predictions,target=/app/data \
  iot-anomaly-api:local
```

Once `docker logs iot-anomaly-api` shows `Application startup complete`,
check the service and replay three readings:

```bash
curl -fsS http://127.0.0.1:8001/health
echo
python -m simulator.stream --url http://127.0.0.1:8001/predict --limit 3
```

The baseline response includes an anomaly score, a threshold near `0.5959`,
and an `is_anomaly` flag. Open [interactive API docs](http://127.0.0.1:8001/docs)
for the request schemas.

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Confirm the API is running with the model loaded |
| `POST /predict` | Score and store one reading |
| `POST /predict/batch` | Score 1–100 readings and store them in one transaction |

## Monitoring

```bash
docker exec -i iot-anomaly-api python - < monitoring/prediction_report.py
docker logs --since 1h iot-anomaly-api 2>&1 | python monitoring/request_report.py
```

The prediction report shows stored readings, the flagged proportion, the
score range, and recent decisions. The request report shows prediction
request volume, 4xx and 5xx error rates, and mean and p95 latency. A batch
counts as one HTTP request and can contain multiple predictions.

## Evaluation

The Isolation Forest was trained on simulated normal readings. The
threshold was selected on the validation set and evaluated on a separate
simulated test set with 1,000 readings, including 55 injected anomalies.

| Model | Anomaly precision | Anomaly recall | Anomaly F1 | Detected | Missed | False alarms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0.581 | 0.655 | 0.615 | 36 | 19 | 26 |
| Retrained candidate | 0.597 | 0.673 | 0.632 | 37 | 18 | 25 |

Both rows use the same simulated test set. Performance on a real
production line still needs to be measured with actual sensor data.

## Retrain and verify a candidate

Provide a fresh CSV of normal readings with the same columns as
`data/normal_train.csv`. Save the candidate to a separate artifact:

```bash
python -m model.train \
  --train-csv data/normal_retrain.csv \
  --artifact model/isolation_forest_candidate.joblib
```

Start a separate container on port `8002` and copy the candidate into it:

```bash
docker create --name iot-anomaly-candidate \
  -p 127.0.0.1:8002:8000 iot-anomaly-api:local

MSYS_NO_PATHCONV=1 docker cp model/isolation_forest_candidate.joblib \
  iot-anomaly-candidate:/app/model/isolation_forest.joblib &&
docker start iot-anomaly-candidate
```

Wait for `Application startup complete` in `docker logs iot-anomaly-candidate`,
then send a reading:

```bash
python -m simulator.stream --url http://127.0.0.1:8002/predict --limit 1
```

Compare the returned threshold with the training output. The candidate
evaluated above returned a threshold near `0.6025`.

See the [architecture](docs/architecture.md) and
[baseline evaluation](docs/model-evaluation.md) for more detail.
