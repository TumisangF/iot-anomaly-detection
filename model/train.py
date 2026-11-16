from pathlib import Path

import joblib
import numpy as np
import pandas as pd

import mlflow
from sklearn.metrics import precision_recall_fscore_support

from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_curve

from simulator.generate_data import OUTPUT_PATH

FEATURES = ["temperature_c", "humidity_pct", "sound_db"]
ARTIFACT_PATH = Path(__file__).resolve().with_name("isolation_forest.joblib")


def main():
    train = pd.read_csv(OUTPUT_PATH)
    validation = pd.read_csv(OUTPUT_PATH.parent / "validation.csv")
    test = pd.read_csv(OUTPUT_PATH.parent / "test.csv")

    model = IsolationForest(n_estimators=100, random_state=42)
    model.fit(train[FEATURES])

    # Reverse scikit-learn's score direction so higher means more unusual.
    validation_scores = -model.score_samples(validation[FEATURES])
    precision, recall, thresholds = precision_recall_curve(
        validation["is_anomaly"], validation_scores
    )

    # The final precision-recall point has no corresponding threshold.
    precision = precision[:-1]
    recall = recall[:-1]
    total = precision + recall
    f1 = np.divide(
        2 * precision * recall,
        total,
        out=np.zeros_like(total),
        where=total > 0,
    )
    best_index = int(np.argmax(f1))
    threshold = float(thresholds[best_index])

    test_scores = -model.score_samples(test[FEATURES])
    predictions = (test_scores >= threshold).astype(int)
    test_labels = test["is_anomaly"]

    print(f"Validation threshold: {threshold:.4f}")
    print(f"Validation anomaly F1: {f1[best_index]:.3f}")
    print("\nHeld-out test results")
    print(classification_report(
        test_labels,
        predictions,
        labels=[0, 1],
        target_names=["normal", "anomaly"],
        digits=3,
        zero_division=0,
    ))
    print("Confusion matrix (actual rows, predicted columns; normal then anomaly)")
    print(confusion_matrix(test_labels, predictions, labels=[0, 1]))

    joblib.dump(
        {"model": model, "features": FEATURES, "threshold": threshold},
        ARTIFACT_PATH,
    )
    print(f"\nSaved model to {ARTIFACT_PATH}")

    test_precision, test_recall, test_f1, _ = precision_recall_fscore_support(
        test_labels,
        predictions,
        average="binary",
        zero_division=0,
    )
    tn, fp, fn, tp = confusion_matrix(test_labels, predictions, labels=[0, 1]).ravel()

    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("iot-anomaly-detection")

    with mlflow.start_run(run_name="isolation-forest-baseline") as run:
        mlflow.log_params({
            "n_estimators": model.n_estimators,
            "random_state": model.random_state,
            "threshold": threshold,
        })
        mlflow.log_metrics({
            "validation_anomaly_f1": float(f1[best_index]),
            "test_anomaly_precision": float(test_precision),
            "test_anomaly_recall": float(test_recall),
            "test_anomaly_f1": float(test_f1),
            "test_true_negatives": int(tn),
            "test_false_positives": int(fp),
            "test_false_negatives": int(fn),
            "test_true_positives": int(tp),
        })
        print(f"Logged MLflow run: {run.info.run_id}")



if __name__ == "__main__":
    main()