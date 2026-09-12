"""Fixed-model uncertainty and descriptive diagnostics; no model fitting."""

from statistics import NormalDist

import numpy as np
from sklearn.metrics import roc_auc_score

from topvistos.modeling import classification_metrics


def wilson_interval(successes, total, confidence=0.95):
    if total < 0 or successes < 0 or successes > total or not 0 < confidence < 1:
        raise ValueError("Invalid binomial counts or confidence level.")
    if total == 0:
        return None
    z = NormalDist().inv_cdf(0.5 + confidence / 2)
    proportion = successes / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    radius = z * np.sqrt(proportion * (1 - proportion) / total + z * z / (4 * total * total)) / denominator
    return [max(0.0, float(center - radius)), min(1.0, float(center + radius))]


def macro_f1(labels, predictions):
    """Binary macro F1 from counts, for repeated bootstrap calculations."""
    y, predicted = np.asarray(labels), np.asarray(predictions)
    tn = np.count_nonzero((y == 0) & (predicted == 0))
    tp = np.count_nonzero((y == 1) & (predicted == 1))
    errors = np.count_nonzero(y != predicted)
    return float(0.5 * (2 * tn / (2 * tn + errors) + 2 * tp / (2 * tp + errors)))


def bootstrap_intervals(labels, probabilities, thresholds, resamples=1000, seed=20260912, confidence=0.95):
    y = np.asarray(labels)
    if resamples < 2 or not 0 < confidence < 1:
        raise ValueError("Need at least two resamples and confidence in (0,1).")
    if set(probabilities) != set(thresholds):
        raise ValueError("Probability and threshold model names differ.")
    for name, values in probabilities.items():
        classification_metrics(y, values, thresholds[name])
    rng = np.random.default_rng(seed)
    strata = [np.flatnonzero(y == label) for label in (0, 1)]
    predicted = {name: (np.asarray(p) >= thresholds[name]).astype(int) for name, p in probabilities.items()}
    samples = {name + "_f1_macro": [] for name in probabilities}
    samples.update(selected_roc_auc=[], selected_brier_score=[], delta_f1_selected_minus_logistic=[])
    for _ in range(resamples):
        indexes = np.concatenate([rng.choice(group, len(group), replace=True) for group in strata])
        drawn_labels = y[indexes]
        scores = {name: macro_f1(drawn_labels, values[indexes]) for name, values in predicted.items()}
        for name, value in scores.items():
            samples[name + "_f1_macro"].append(value)
        selected = np.asarray(probabilities["selected_boosting"])[indexes]
        samples["selected_roc_auc"].append(float(roc_auc_score(drawn_labels, selected)))
        samples["selected_brier_score"].append(float(np.mean((selected - drawn_labels) ** 2)))
        samples["delta_f1_selected_minus_logistic"].append(scores["selected_boosting"] - scores["logistic_regression"])
    quantiles = [(1 - confidence) / 2, (1 + confidence) / 2]
    return {
        "method": "paired class-stratified percentile bootstrap",
        "resamples": resamples, "seed": seed, "confidence": confidence,
        "scope": "Conditional on fixed models and observed class counts; excludes training and selection uncertainty.",
        "intervals": {name: np.quantile(values, quantiles).tolist() for name, values in samples.items()},
    }


def calibration_summary(labels, probabilities, bins=10):
    y, p = np.asarray(labels), np.asarray(probabilities, dtype=float)
    classification_metrics(y, p)
    if not isinstance(bins, int) or bins < 1:
        raise ValueError("Bin count must be a positive integer.")
    edges = np.linspace(0, 1, bins + 1)
    assigned = np.minimum(np.searchsorted(edges, p, side="right") - 1, bins - 1)
    result, error = [], 0.0
    for index in range(bins):
        mask = assigned == index
        count = int(mask.sum())
        mean = float(p[mask].mean()) if count else None
        observed = float(y[mask].mean()) if count else None
        if count:
            error += count * abs(mean - observed)
        result.append({
            "lower": float(edges[index]), "upper": float(edges[index + 1]),
            "upper_inclusive": index == bins - 1, "rows": count,
            "mean_probability": mean, "observed_approval_rate": observed,
            "observed_rate_wilson95": wilson_interval(int(y[mask].sum()), count),
        })
    return {"bins": result, "ece": float(error / len(y)),
            "ece_definition": "Sum of bin-count weights times absolute predicted-minus-observed approval rate."}


def segment_summary(frame, labels, probabilities, threshold, columns, min_rows=100, min_class=20):
    y, p = np.asarray(labels), np.asarray(probabilities)
    classification_metrics(y, p, threshold)
    if len(frame) != len(y) or min_rows < 1 or min_class < 1:
        raise ValueError("Invalid segment alignment or minimum support.")
    groups = {}
    for column in columns:
        values = frame[column].astype("string").fillna("<missing>").to_numpy()
        entries = []
        for category in sorted(set(values)):
            mask = values == category
            count = int(mask.sum())
            denied, approved = int((y[mask] == 0).sum()), int((y[mask] == 1).sum())
            entry = {"category": str(category), "rows": count, "denied": denied, "approved": approved}
            if count < min_rows or min(denied, approved) < min_class:
                entry.update(metrics=None, suppression_reason="Below predefined row or per-class support.")
            else:
                metrics = classification_metrics(y[mask], p[mask], threshold)
                matrix = metrics["confusion_matrix"]
                entry.update(
                    metrics=metrics,
                    recall_denied_wilson95=wilson_interval(matrix[0][0], denied),
                    recall_approved_wilson95=wilson_interval(matrix[1][1], approved),
                )
            entries.append(entry)
        groups[column] = entries
    return {"minimum_rows": min_rows, "minimum_per_class": min_class, "groups": groups,
            "scope": "Descriptive overlapping segments; no multiple-comparison correction or causal interpretation."}