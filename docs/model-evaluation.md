# Isolation Forest baseline

The model was fitted on 2,000 simulated normal readings. The anomaly
threshold (0.5959, rounded) was selected by maximizing anomaly F1 on
the validation set, then applied to a separate 1,000-reading test set.

| Test metric | Result |
| --- | ---: |
| Anomaly precision | 0.581 |
| Anomaly recall | 0.655 |
| Anomaly F1 | 0.615 |

| Actual class | Predicted normal | Predicted anomaly |
| --- | ---: | ---: |
| Normal | 919 | 26 |
| Anomaly | 19 | 36 |

The model caught 36 of 55 anomalous readings. These results measure
detection of injected anomalies in simulated data. Performance on a
real production line remains unmeasured.
