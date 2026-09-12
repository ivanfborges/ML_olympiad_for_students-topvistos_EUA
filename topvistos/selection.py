"""Bounded model selection on training CV, then threshold selection on validation."""

import argparse
from importlib.metadata import version
import json
from pathlib import Path
import platform
import warnings

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.model_selection import StratifiedKFold, cross_validate
from threadpoolctl import threadpool_limits

from scripts.inspect_data import FEATURES, TARGET
from topvistos.baseline import PACKAGES
from topvistos.data import load_labeled, partition_fingerprint, sha256_file, split_labeled
from topvistos.modeling import build_logistic, classification_metrics

ROOT = Path(__file__).resolve().parents[1]


def build_candidate(specification, seed=42):
    """Reuse baseline preprocessing; dense one-hot input for tree models."""
    pipeline = build_logistic(seed)
    family = specification["family"]
    parameters = specification["parameters"]
    if family == "logistic":
        pipeline.set_params(**{"model__" + key: value for key, value in parameters.items()})
    else:
        if family == "random_forest":
            model = RandomForestClassifier(random_state=seed, **parameters)
        elif family == "hist_gradient_boosting":
            model = HistGradientBoostingClassifier(random_state=seed, **parameters)
        else:
            raise ValueError(f"Unknown model family: {family}")
        pipeline.set_params(
            model=model, preprocess__categorical__encode__sparse_output=False,
            preprocess__sparse_threshold=0.0,
        )
    return pipeline


def choose_candidate(results):
    """Use CV only. Validation scores cannot influence this decision."""
    if not results:
        raise ValueError("At least one candidate is required.")
    scores = np.asarray([item["training_cv"]["f1_macro"]["mean"] for item in results])
    if not np.isfinite(scores).all():
        raise ValueError("Candidate CV scores must be finite.")
    best = float(scores.max())
    return next(item["id"] for item, score in zip(results, scores) if best - score <= 1e-12)


def score_at_half(estimator, features, labels):
    """Use the same >= 0.5 rule in CV and validation, including exact ties."""
    metrics = classification_metrics(labels, estimator.predict_proba(features)[:, 1], 0.5)
    return {name: metrics[name] for name in ("f1_macro", "balanced_accuracy", "roc_auc")}


def compare_training(train, config):
    """This function has no validation or final-holdout argument."""
    folds = StratifiedKFold(n_splits=config["cv_folds"], shuffle=True, random_state=config["seed"])
    metrics = ("f1_macro", "balanced_accuracy", "roc_auc")
    results = []
    for spec in config["candidates"]:
        scores = cross_validate(
            build_candidate(spec, config["seed"]), train[FEATURES], train[TARGET],
            cv=folds, scoring=score_at_half, n_jobs=1, error_score="raise",
        )
        summary = {
            metric: {
                "fold_scores": scores["test_" + metric].tolist(),
                "mean": float(np.mean(scores["test_" + metric])),
                "std": float(np.std(scores["test_" + metric], ddof=1)),
            }
            for metric in metrics
        }
        results.append({**spec, "training_cv": summary})
        print(f'{spec["id"]}: training-CV macro F1 = {summary["f1_macro"]["mean"]:.6f}', flush=True)
    return results, choose_candidate(results)


def select_threshold(labels, probabilities, thresholds):
    """Tune only the decision rule on separate validation predictions."""
    grid = np.asarray(thresholds, dtype=float)
    if grid.ndim != 1 or not grid.size or not np.isfinite(grid).all():
        raise ValueError("Thresholds must be a nonempty finite 1D grid.")
    if np.any((grid < 0) | (grid > 1)) or len(set(grid)) != len(grid):
        raise ValueError("Thresholds must be unique and in [0, 1].")
    curve = [
        {"threshold": float(value), **classification_metrics(labels, probabilities, float(value))}
        for value in grid
    ]
    best_score = max(point["f1_macro"] for point in curve)
    tied = [point for point in curve if best_score - point["f1_macro"] <= 1e-12]
    selected = min(tied, key=lambda point: (round(abs(point["threshold"] - 0.5), 12), point["threshold"]))
    return selected, curve


def check_partitions(partitions, baseline):
    """Check identities only; never inspect reserved holdout features/labels."""
    actual = {
        name: {
            "rows": len(getattr(partitions, name)),
            "membership_sha256": partition_fingerprint(getattr(partitions, name)),
        }
        for name in ("train", "validation", "holdout")
    }
    if actual != baseline["partitions"]:
        raise ValueError("Partition membership differs from the recorded baseline.")
    return actual


def write_plot(report, output_path):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    figure, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    candidates = report["candidates"]
    ids = [item["id"] for item in candidates]
    means = [item["training_cv"]["f1_macro"]["mean"] for item in candidates]
    colors = ["#167b86" if name == report["selected_id"] else "#91a5b5" for name in ids]
    bars = axes[0].barh(ids, means, color=colors)
    axes[0].bar_label(bars, fmt="%.3f", padding=3)
    axes[0].invert_yaxis()
    axes[0].set_xlim(0, 1)
    axes[0].set_title("Model selection: training CV")
    axes[0].set_xlabel("Mean macro F1 at threshold 0.5")
    curve = report["threshold_curve"]
    for metric, label, color in [
        ("f1_macro", "Macro F1", "#167b86"),
        ("recall_denied", "Denied recall", "#b35a27"),
        ("recall_approved", "Approved recall", "#5673a1"),
    ]:
        axes[1].plot([p["threshold"] for p in curve], [p[metric] for p in curve],
                     label=label, color=color, linewidth=2)
    axes[1].axvline(report["selected_threshold"], color="#475569", linestyle="--",
                    label=f'Selected: {report["selected_threshold"]:.3f}')
    axes[1].set(title="Threshold selection: validation", xlabel="Approval threshold", ylim=(0, 1.04))
    axes[1].legend(fontsize=8, loc="lower left")
    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="x", alpha=0.15)
        axis.set_axisbelow(True)
    figure.suptitle("TopVistos: bounded model and threshold selection")
    figure.text(0.5, 0.015, "Development results include selection bias | Final holdout not evaluated",
                ha="center", fontsize=9, color="#475569")
    figure.tight_layout(rect=(0, 0.04, 1, 0.95))
    figure.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def run(data_dir, output_dir):
    config_path = ROOT / "configs/selection.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if (config["protocol_version"], config["primary_metric"], config["cv_threshold"]) != (1, "f1_macro", 0.5):
        raise ValueError("Unsupported selection protocol.")
    ids = [spec["id"] for spec in config["candidates"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Candidate IDs must be unique.")
    baseline = json.loads((ROOT / "docs/baseline/metrics.json").read_text(encoding="utf-8"))
    data_hash = baseline["data_sha256"]
    frame = load_labeled(data_dir / "train.csv", data_hash)
    partitions = split_labeled(frame, seed=config["seed"])
    membership = check_partitions(partitions, baseline)

    with threadpool_limits(limits=1), warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        candidates, selected_id = compare_training(partitions.train, config)
        spec = next(item for item in config["candidates"] if item["id"] == selected_id)
        fitted = build_candidate(spec, config["seed"])
        fitted.fit(partitions.train[FEATURES], partitions.train[TARGET])
        probabilities = fitted.predict_proba(partitions.validation[FEATURES])[:, 1]
        default_metrics = classification_metrics(partitions.validation[TARGET], probabilities)
        selected, curve = select_threshold(partitions.validation[TARGET], probabilities, config["thresholds"])

    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / "selected_pipeline.joblib"
    joblib.dump(fitted, model_path)
    restored = joblib.load(model_path)  # Trusted artifact just created locally.
    with threadpool_limits(limits=1):
        restored_probabilities = restored.predict_proba(partitions.validation[FEATURES])[:, 1]
    np.testing.assert_allclose(probabilities, restored_probabilities, rtol=0, atol=0)
    source_paths = [
        "configs/selection.json", "requirements-lock.txt", "scripts/inspect_data.py",
        "topvistos/data.py", "topvistos/modeling.py", "topvistos/baseline.py", "topvistos/selection.py",
    ]
    report = {
        "phase": "development_selection",
        "config": config,
        "data_sha256": data_hash,
        "baseline_report_sha256": sha256_file(ROOT / "docs/baseline/metrics.json"),
        "source_sha256": {name: sha256_file(ROOT / name) for name in source_paths},
        "environment": {
            "python": platform.python_version(), "system": platform.system(),
            "packages": {name: version(name) for name in PACKAGES}, "numeric_thread_limit": 1,
        },
        "partitions": membership,
        "holdout_evaluated": False,
        "candidates": candidates,
        "selected_id": selected_id,
        "selected_threshold": selected["threshold"],
        "validation_default": default_metrics,
        "validation_selected": {key: value for key, value in selected.items() if key != "threshold"},
        "threshold_curve": curve,
        "frozen_model": {
            "file": "selected_pipeline.joblib", "sha256": sha256_file(model_path),
            "training_partition_only": True,
            "serialization_check": "Exact probabilities on every validation case after reload.",
        },
        "limitations": [
            "Winning CV and threshold-selected validation scores are subject to selection bias.",
            "Final holdout has not been evaluated; no leaderboard claim is made.",
            "Macro F1 is an internal objective, not a verified competition metric or business cost.",
            "Only seven fixed configurations were compared; no broad optimality claim.",
            "Random case partitions do not test future years or unseen employer groups.",
            "The dataset was historically explored; this holdout is not new external data.",
            "Probability calibration, subgroup analysis and deployment validation remain pending.",
        ],
    }
    (output_dir / "metrics.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    decision = {
        "selected_id": selected_id, "specification": spec,
        "threshold": selected["threshold"], "positive_label": "Aprovado",
        "prediction_rule": "approval_probability >= threshold",
        "model_sha256": report["frozen_model"]["sha256"],
        "data_sha256": data_hash, "partitions": membership,
        "source_sha256": report["source_sha256"], "holdout_evaluated": False,
        "refit_on_validation": False,
    }
    (output_dir / "decision.json").write_text(
        json.dumps(decision, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    write_plot(report, output_dir / "selection.png")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/raw")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports/generated/selection")
    args = parser.parse_args()
    report = run(args.data_dir, args.output_dir)
    print(json.dumps({key: report[key] for key in (
        "selected_id", "selected_threshold", "holdout_evaluated",
        "validation_default", "validation_selected",
    )}, indent=2))


if __name__ == "__main__":
    main()