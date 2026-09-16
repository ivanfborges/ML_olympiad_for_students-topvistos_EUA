"""Predict with a trusted pipeline and its recorded decision; never train."""

import argparse
import csv
from importlib.metadata import version
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from scripts.inspect_data import FEATURES, IDENTIFIER
from topvistos.data import sha256_file
from topvistos.modeling import normalize_features

ROOT = Path(__file__).resolve().parents[1]


def validate_input(frame):
    expected = [IDENTIFIER, *FEATURES]
    if list(frame.columns) != expected or frame.empty:
        raise ValueError("Expected nonempty input with exactly id_do_caso followed by the ten features; no target.")
    ids = frame[IDENTIFIER]
    if ids.isna().any() or any(not isinstance(value, str) or not value.strip() for value in ids):
        raise ValueError("Case identifiers must be nonblank strings.")
    if ids.str.strip().duplicated().any():
        raise ValueError("Case identifiers must be unique.")
    normalize_features(frame[FEATURES])
    return frame


def read_input(path):
    # Check original headers and row widths before pandas can rename duplicates.
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        rows = csv.reader(stream)
        header = next(rows, [])
        if header != [IDENTIFIER, *FEATURES]:
            raise ValueError("Unexpected input CSV header.")
        if any(len(row) != len(header) for row in rows):
            raise ValueError("Malformed CSV row.")
    frame = pd.read_csv(path, encoding="utf-8-sig", dtype={IDENTIFIER: str}, keep_default_na=False)
    # Preserve literal IDs such as NA; empty feature cells represent missing data.
    frame[FEATURES] = frame[FEATURES].replace("", np.nan)
    return validate_input(frame)


def load_bundle(model_path, decision_path):
    decision = json.loads(Path(decision_path).read_text(encoding="utf-8"))
    recorded = json.loads((ROOT / "docs/selection/decision.json").read_text(encoding="utf-8"))
    # A rebuilt artifact may have a new byte hash, but cannot change the selected protocol.
    for key in ("selected_id", "specification", "threshold", "positive_label", "prediction_rule",
                "data_sha256", "partitions", "source_sha256", "refit_on_validation"):
        if decision.get(key) != recorded[key]:
            raise ValueError(f"Decision differs from the recorded protocol: {key}")
    for name, digest in decision["source_sha256"].items():
        if sha256_file(ROOT / name) != digest:
            raise ValueError(f"Training source hash mismatch: {name}")
    environment = json.loads((ROOT / "docs/selection/metrics.json").read_text(encoding="utf-8"))["environment"]
    for name, expected in environment["packages"].items():
        if version(name) != expected:
            raise ValueError(f"Dependency version mismatch: {name}")
    if sha256_file(model_path) != decision.get("model_sha256"):
        raise ValueError("Model hash does not match its decision file.")
    model = joblib.load(model_path)  # Only trusted local artifacts; a hash is not a trust guarantee.
    estimator = getattr(model, "named_steps", {}).get("model")
    if estimator is None or type(estimator).__name__ != "HistGradientBoostingClassifier":
        raise ValueError("Expected the selected histogram boosting pipeline.")
    parameters = estimator.get_params()
    if any(parameters.get(name) != value for name, value in recorded["specification"]["parameters"].items()):
        raise ValueError("Model parameters differ from the recorded specification.")
    if list(model.classes_) != [0, 1]:
        raise ValueError("Expected probability columns for classes [0, 1].")
    origin = "recorded" if decision["model_sha256"] == recorded["model_sha256"] else "rebuilt"
    return model, decision["threshold"], origin


def predict_frame(frame, model, threshold, origin):
    validate_input(frame)
    if not np.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("Invalid decision threshold.")
    with threadpool_limits(limits=1):
        probabilities = np.asarray(model.predict_proba(frame[FEATURES]))
    if probabilities.shape != (len(frame), 2) or not np.isfinite(probabilities).all():
        raise ValueError("Invalid model probabilities.")
    if np.any((probabilities < 0) | (probabilities > 1)) or not np.allclose(probabilities.sum(axis=1), 1):
        raise ValueError("Invalid probability distribution.")
    approved = probabilities[:, 1]
    return pd.DataFrame({
        IDENTIFIER: frame[IDENTIFIER].to_numpy(),
        "approval_probability": approved,
        "predicted_status": np.where(approved >= threshold, "Aprovado", "Negado"),
        "decision_threshold": threshold,
        "artifact_origin": origin,
    })


def run(input_path, model_path, decision_path, output_path):
    if output_path.exists():
        raise FileExistsError("Output already exists; choose a new path.")
    frame = read_input(input_path)
    model, threshold, origin = load_bundle(model_path, decision_path)
    result = predict_frame(frame, model, threshold, origin)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8", newline="") as stream:
        result.to_csv(stream, index=False)
    return {"rows": len(result), "threshold": threshold, "artifact_origin": origin, "output": str(output_path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--decision", type=Path, default=ROOT / "docs/selection/decision.json")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/generated/inference/predictions.csv")
    parser.add_argument("--check-input", action="store_true", help="Validate input without loading a model.")
    args = parser.parse_args()
    try:
        if args.check_input:
            print(json.dumps({"rows": len(read_input(args.input)), "input_valid": True, "prediction_performed": False}))
        else:
            if args.model is None:
                parser.error("--model is required unless --check-input is used.")
            print(json.dumps(run(args.input, args.model, args.decision, args.output)))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()