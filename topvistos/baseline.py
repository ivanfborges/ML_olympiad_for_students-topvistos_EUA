"""Run fixed baselines on training/validation data; do not evaluate the holdout."""

import argparse
from importlib.metadata import version
import json
from pathlib import Path
import platform
import warnings

import joblib
import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import f1_score, make_scorer
from sklearn.model_selection import StratifiedKFold, cross_validate
from threadpoolctl import threadpool_limits

from scripts.inspect_data import FEATURES, IDENTIFIER, TARGET
from topvistos.data import (
    load_labeled, partition_fingerprint, sha256_file, split_labeled, training_quality,
)
from topvistos.modeling import build_candidates, classification_metrics

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ["numpy", "pandas", "scikit-learn", "scipy", "joblib", "matplotlib", "threadpoolctl"]


def evaluate_development(train, validation, seed=42):
    """The function deliberately receives no holdout features or labels."""
    X_train, y_train = train[FEATURES], train[TARGET]
    X_validation, y_validation = validation[FEATURES], validation[TARGET]
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    scoring = {
        "f1_macro": make_scorer(f1_score, average="macro", zero_division=0),
        "f1_approved": make_scorer(f1_score, pos_label=1, zero_division=0),
        "balanced_accuracy": "balanced_accuracy",
        "roc_auc": "roc_auc",
    }
    results, fitted = {}, {}
    for name, estimator in build_candidates(seed).items():
        scores = cross_validate(
            estimator, X_train, y_train, cv=folds, scoring=scoring,
            n_jobs=1, error_score="raise",
        )
        estimator.fit(X_train, y_train)
        probabilities = estimator.predict_proba(X_validation)[:, 1]
        results[name] = {
            "training_cv": {
                metric: {
                    "fold_scores": scores["test_" + metric].tolist(),
                    "mean": float(np.mean(scores["test_" + metric])),
                    "std": float(np.std(scores["test_" + metric], ddof=1)),
                }
                for metric in scoring
            },
            "validation": classification_metrics(y_validation, probabilities),
        }
        fitted[name] = estimator
    return results, fitted


def write_plot(results, output_path):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    names = ["prior_baseline", "logistic_regression"]
    labels = ["Prior baseline", "Logistic regression"]
    metrics = [("f1_macro", "Macro F1"), ("roc_auc", "ROC-AUC"), ("recall_denied", "Denied recall")]
    figure, axes = plt.subplots(1, 3, figsize=(10.5, 3.8), sharey=True)
    for axis, (metric, title) in zip(axes, metrics):
        values = [results[name]["validation"][metric] for name in names]
        bars = axis.bar(labels, values, color=["#91a5b5", "#167b86"], width=0.58)
        axis.bar_label(bars, fmt="%.3f", padding=4, fontsize=10)
        axis.set_title(title)
        axis.set_ylim(0, 1.08)
        axis.spines[["top", "right"]].set_visible(False)
        axis.tick_params(axis="x", labelsize=9)
        axis.set_axisbelow(True)
        axis.grid(axis="y", alpha=0.15)
    axes[0].set_ylabel("Score")
    figure.suptitle("TopVistos: fixed baselines on the validation partition", fontsize=13)
    figure.text(0.5, 0.02, "Decision threshold: 0.5 | Final holdout not evaluated | Higher is better",
                ha="center", fontsize=9, color="#475569")
    figure.tight_layout(rect=(0, 0.06, 1, 0.94))
    figure.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def run(data_dir, output_dir):
    config = json.loads((ROOT / "configs" / "baseline.json").read_text(encoding="utf-8"))
    # A new selection protocol needs a deliberate code/config change.
    if config != {
        "protocol_version": 1, "seed": 42, "split_fractions": [0.6, 0.2, 0.2],
        "cv_folds": 5, "decision_threshold": 0.5, "logistic_C": 1.0,
        "primary_development_metric": "f1_macro",
    }:
        raise ValueError("Configuration differs from the implemented fixed-baseline protocol.")
    manifest = json.loads((ROOT / "docs" / "data-manifest.json").read_text(encoding="utf-8"))
    frame = load_labeled(data_dir / "train.csv", manifest["files"]["train.csv"]["sha256"])
    partitions = split_labeled(frame, seed=config["seed"])
    with threadpool_limits(limits=1), warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        results, fitted = evaluate_development(
            partitions.train, partitions.validation, seed=config["seed"]
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    split_ids = {
        name: getattr(partitions, name)[IDENTIFIER].tolist()
        for name in ("train", "validation", "holdout")
    }
    (output_dir / "split_ids.json").write_text(json.dumps(split_ids), encoding="utf-8")
    source_paths = [
        "configs/baseline.json", "requirements-lock.txt", "scripts/inspect_data.py",
        "topvistos/data.py", "topvistos/modeling.py", "topvistos/baseline.py",
    ]
    report = {
        "phase": "development_baseline",
        "config": config,
        "data_sha256": manifest["files"]["train.csv"]["sha256"],
        "source_sha256": {path: sha256_file(ROOT / path) for path in source_paths},
        "environment": {
            "python": platform.python_version(),
            "system": platform.system(),
            "packages": {name: version(name) for name in PACKAGES},
            "numeric_thread_limit": 1,
        },
        "partitions": {
            name: {
                "rows": len(getattr(partitions, name)),
                "membership_sha256": partition_fingerprint(getattr(partitions, name)),
            }
            for name in split_ids
        },
        "holdout_evaluated": False,
        "training_data_quality": training_quality(partitions.train),
        "results": results,
        "limitations": [
            "Metrics are development results, not final-test scores or a Kaggle leaderboard result.",
            "Macro F1 is an internal criterion; the official competition F1 variant is unverified.",
            "A random case split assumes exchangeable cases; no temporal or employer-group holdout is available.",
            "The source dataset was explored historically; the holdout is reserved within this reconstruction, not new external data.",
            "Negative employee counts become missing with an indicator; wages retain their original units.",
            "No hyperparameter or threshold search, calibration, subgroup audit, or deployment validation was performed.",
        ],
    }
    for name, estimator in fitted.items():
        path = output_dir / (name + ".joblib")
        joblib.dump(estimator, path)
        reloaded = joblib.load(path)  # Trusted, locally created artifact.
        row = partitions.validation[FEATURES].iloc[:3]
        np.testing.assert_array_equal(
            estimator.predict_proba(row), reloaded.predict_proba(row)
        )
    report["serialization_check"] = "Exact probability equality on three validation rows for each baseline."
    (output_dir / "metrics.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_plot(results, output_dir / "validation-baselines.png")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports" / "generated" / "baseline")
    args = parser.parse_args()
    report = run(args.data_dir, args.output_dir)
    print(json.dumps({
        "phase": report["phase"], "holdout_evaluated": report["holdout_evaluated"],
        "partition_rows": {name: part["rows"] for name, part in report["partitions"].items()},
        "validation": {name: result["validation"] for name, result in report["results"].items()},
    }, indent=2))


if __name__ == "__main__":
    main()