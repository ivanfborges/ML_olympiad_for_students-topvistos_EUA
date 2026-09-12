"""Training-local preprocessing and fixed binary-classification baselines."""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, average_precision_score, balanced_accuracy_score,
    brier_score_loss, confusion_matrix, f1_score, precision_score,
    recall_score, roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.validation import check_is_fitted

from scripts.inspect_data import FEATURES

NUMERIC = ["num_de_empregados", "ano_de_estabelecimento", "salario_prevalecente"]
CATEGORICAL = [name for name in FEATURES if name not in NUMERIC]
INVALID_COUNT = "employee_count_invalid"


def normalize_features(frame):
    """Apply deterministic domain rules, without estimating dataset statistics."""
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise ValueError("Features must be a nonempty pandas DataFrame.")
    if len(frame.columns) != len(set(frame.columns)) or set(frame.columns) != set(FEATURES):
        raise ValueError("Expected exactly the documented features; exclude IDs and target.")
    result = frame.loc[:, FEATURES].copy()
    for column in NUMERIC:
        values = pd.to_numeric(result[column], errors="raise").astype(float)
        if not np.isfinite(values.dropna()).all():
            raise ValueError(f"{column}: infinite values are not supported.")
        result[column] = values
    invalid = result["num_de_empregados"] < 0
    result[INVALID_COUNT] = invalid.astype(float)
    result.loc[invalid, "num_de_empregados"] = np.nan
    for column in CATEGORICAL:
        values = result[column]
        nonmissing = values.dropna()
        if any(not isinstance(value, str) for value in nonmissing):
            raise ValueError(f"{column}: expected strings or missing values.")
        result[column] = values.astype(object).where(values.notna(), np.nan)
    return result


class FeaturePolicy(TransformerMixin, BaseEstimator):
    """Stateless domain policy inside the serialized sklearn pipeline."""

    def fit(self, X, y=None):
        normalize_features(X)
        self.feature_names_in_ = np.asarray(FEATURES, dtype=object)
        self.n_features_in_ = len(FEATURES)
        return self

    def transform(self, X):
        check_is_fitted(self)
        return normalize_features(X)


def build_logistic(seed=42):
    numeric = Pipeline([
        ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
        ("scale", StandardScaler()),
    ])
    categorical = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encode", OneHotEncoder(handle_unknown="ignore")),
    ])
    preprocess = ColumnTransformer([
        ("numeric", numeric, [*NUMERIC, INVALID_COUNT]),
        ("categorical", categorical, CATEGORICAL),
    ])
    return Pipeline([
        ("feature_policy", FeaturePolicy()),
        ("preprocess", preprocess),
        ("model", LogisticRegression(
            C=1.0, solver="lbfgs", max_iter=2000, random_state=seed,
        )),
    ])


def build_candidates(seed=42):
    return {
        "prior_baseline": DummyClassifier(strategy="prior"),
        "logistic_regression": build_logistic(seed),
    }


def classification_metrics(labels, probabilities, threshold=0.5):
    """Class 1 is approved; scores use probabilities and errors use labels."""
    y = np.asarray(labels)
    p = np.asarray(probabilities, dtype=float)
    if y.ndim != 1 or p.shape != y.shape or not y.size:
        raise ValueError("Labels and probabilities must be matching 1D arrays.")
    if set(np.unique(y)) != {0, 1}:
        raise ValueError("Evaluation requires both binary classes.")
    if not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError("Probabilities must be finite and in [0, 1].")
    if not np.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("Threshold must be in [0, 1].")
    predictions = (p >= threshold).astype(int)
    return {
        "f1_macro": float(f1_score(y, predictions, average="macro", zero_division=0)),
        "f1_approved": float(f1_score(y, predictions, pos_label=1, zero_division=0)),
        "accuracy": float(accuracy_score(y, predictions)),
        "balanced_accuracy": float(balanced_accuracy_score(y, predictions)),
        "roc_auc": float(roc_auc_score(y, p)),
        "average_precision_approved": float(average_precision_score(y, p)),
        "brier_score": float(brier_score_loss(y, p)),
        "precision_approved": float(precision_score(y, predictions, pos_label=1, zero_division=0)),
        "recall_approved": float(recall_score(y, predictions, pos_label=1, zero_division=0)),
        "precision_denied": float(precision_score(y, predictions, pos_label=0, zero_division=0)),
        "recall_denied": float(recall_score(y, predictions, pos_label=0, zero_division=0)),
        "confusion_matrix": confusion_matrix(y, predictions, labels=[0, 1]).tolist(),
        "confusion_matrix_order": ["denied_0", "approved_1"],
        "predicted_approval_rate": float(predictions.mean()),
    }