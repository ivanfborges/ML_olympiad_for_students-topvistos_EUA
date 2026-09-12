"""Evaluate already-frozen models once on the recorded final holdout."""

import argparse
from importlib.metadata import version
import json
from pathlib import Path
import platform

import joblib
import numpy as np
from threadpoolctl import threadpool_limits

from scripts.inspect_data import FEATURES, TARGET
from topvistos.baseline import PACKAGES
from topvistos.data import load_labeled, sha256_file, split_labeled
from topvistos.evaluation_stats import bootstrap_intervals, calibration_summary, segment_summary
from topvistos.modeling import classification_metrics
from topvistos.selection import check_partitions

ROOT = Path(__file__).resolve().parents[1]


def load_frozen_models(model_paths, config, decision, recorded_environment, root=ROOT):
    """Validate every artifact before deserializing trusted local model files."""
    selected = config["models"]["selected_boosting"]
    if selected["sha256"] != decision["model_sha256"] or selected["threshold"] != decision["threshold"]:
        raise ValueError("Evaluation differs from the frozen model or threshold.")
    if decision["refit_on_validation"] or decision["prediction_rule"] != "approval_probability >= threshold":
        raise ValueError("Unexpected frozen decision rule.")
    if set(model_paths) != set(config["models"]):
        raise ValueError("Expected exactly the three preregistered artifacts.")
    for name, digest in decision["source_sha256"].items():
        if sha256_file(root / name) != digest:
            raise ValueError(f"Training source hash mismatch: {name}")
    for name, expected in recorded_environment["packages"].items():
        if version(name) != expected:
            raise ValueError(f"Dependency version differs from recorded training: {name}")
    for name, path in model_paths.items():
        if sha256_file(path) != config["models"][name]["sha256"]:
            raise ValueError(f"Frozen model hash mismatch: {name}")
    models = {name: joblib.load(path) for name, path in model_paths.items()}
    if any(list(model.classes_) != [0, 1] for model in models.values()):
        raise ValueError("Unexpected probability class order.")
    return models


def evaluate_holdout(holdout, models, config):
    """Prediction and diagnostics only; this function never fits an estimator."""
    y = holdout[TARGET].to_numpy()
    thresholds = {name: spec["threshold"] for name, spec in config["models"].items()}
    with threadpool_limits(limits=1):
        probabilities = {name: model.predict_proba(holdout[FEATURES])[:, 1] for name, model in models.items()}
    metrics = {name: classification_metrics(y, p, thresholds[name]) for name, p in probabilities.items()}
    bootstrap = config["bootstrap"]
    uncertainty = bootstrap_intervals(
        y, probabilities, thresholds, resamples=bootstrap["resamples"],
        seed=bootstrap["seed"], confidence=bootstrap["confidence"],
    )
    selected = probabilities["selected_boosting"]
    return {
        "rows": len(y),
        "class_counts": {"denied": int((y == 0).sum()), "approved": int((y == 1).sum())},
        "metrics": metrics,
        "uncertainty": uncertainty,
        "delta_f1_selected_minus_logistic": metrics["selected_boosting"]["f1_macro"] - metrics["logistic_regression"]["f1_macro"],
        "calibration": calibration_summary(y, selected, config["calibration_bins"]),
        "segments": segment_summary(
            holdout, y, selected, thresholds["selected_boosting"], config["segments"],
            min_rows=config["segment_min_rows"], min_class=config["segment_min_per_class"],
        ),
    }, probabilities


def write_plot(report, output_path):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    figure, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    names = ["prior_baseline", "logistic_regression", "selected_boosting"]
    labels = ["Prior / 0.50", "Logistic / 0.50", "Boosting / 0.60"]
    means = [report["metrics"][name]["f1_macro"] for name in names]
    intervals = [report["uncertainty"]["intervals"][name + "_f1_macro"] for name in names]
    axes[0].bar(labels, means, color=["#91a5b5", "#5673a1", "#167b86"])
    for position, (mean, bounds) in enumerate(zip(means, intervals)):
        axes[0].plot([position, position], bounds, color="#243746", linewidth=2)
        axes[0].plot([position - 0.08, position + 0.08], [bounds[0]] * 2, color="#243746")
        axes[0].plot([position - 0.08, position + 0.08], [bounds[1]] * 2, color="#243746")
        axes[0].text(position, bounds[1] + 0.025, f"{mean:.3f}", ha="center")
    axes[0].set(title="Final holdout: macro F1", ylim=(0, 1), ylabel="Score with 95% bootstrap interval")
    bins = [item for item in report["calibration"]["bins"] if item["rows"]]
    x = [item["mean_probability"] for item in bins]
    y = [item["observed_approval_rate"] for item in bins]
    axes[1].plot([0, 1], [0, 1], "--", color="#91a5b5", label="Perfect calibration")
    axes[1].errorbar(x, y, yerr=[
        [value - item["observed_rate_wilson95"][0] for value, item in zip(y, bins)],
        [item["observed_rate_wilson95"][1] - value for value, item in zip(y, bins)],
    ], fmt="o-", color="#167b86", capsize=3, label="Selected boosting; Wilson 95%")
    axes[1].set(title="Calibration: fixed probability bins", xlim=(0, 1), ylim=(0, 1),
                xlabel="Mean predicted approval probability", ylabel="Observed approval fraction")
    axes[1].legend(fontsize=8)
    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="y", alpha=0.15)
        axis.set_axisbelow(True)
    figure.suptitle("TopVistos: evaluation of frozen models")
    figure.text(0.5, 0.01, "Historical random-case holdout | No refitting or threshold changes", ha="center", fontsize=9)
    figure.tight_layout(rect=(0, 0.04, 1, 0.95))
    figure.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def run(data_dir, selection_dir, baseline_dir, output_dir):
    if output_dir.exists():
        raise FileExistsError("Evaluation output exists; preserve it and review saved results.")
    config = json.loads((ROOT / "configs/evaluation.json").read_text(encoding="utf-8"))
    if config["protocol_version"] != 1 or config["primary_metric"] != "f1_macro":
        raise ValueError("Unsupported final evaluation protocol.")
    decision = json.loads((ROOT / "docs/selection/decision.json").read_text(encoding="utf-8"))
    selection = json.loads((ROOT / "docs/selection/metrics.json").read_text(encoding="utf-8"))
    if decision["partitions"] != selection["partitions"] or decision["data_sha256"] != selection["data_sha256"]:
        raise ValueError("Frozen selection records are inconsistent.")
    paths = {
        "prior_baseline": baseline_dir / "prior_baseline.joblib",
        "logistic_regression": baseline_dir / "logistic_regression.joblib",
        "selected_boosting": selection_dir / "selected_pipeline.joblib",
    }
    models = load_frozen_models(paths, config, decision, selection["environment"])
    frame = load_labeled(data_dir / "train.csv", decision["data_sha256"])
    partitions = split_labeled(frame, seed=config["split_seed"])
    membership = check_partitions(partitions, decision)
    report, probabilities = evaluate_holdout(partitions.holdout, models, config)
    report.update(
        phase="final_holdout_evaluation", holdout_evaluated=True, refit_performed=False,
        config=config, partitions=membership, data_sha256=decision["data_sha256"],
        frozen_decision_sha256=sha256_file(ROOT / "docs/selection/decision.json"),
        training_source_sha256=decision["source_sha256"],
        evaluation_source_sha256={name: sha256_file(ROOT / name) for name in (
            "configs/evaluation.json", "topvistos/evaluation.py", "topvistos/evaluation_stats.py",
        )},
        environment={"python": platform.python_version(), "system": platform.system(),
                     "packages": {name: version(name) for name in PACKAGES}, "numeric_thread_limit": 1},
        limitations=[
            "The final holdout is now consumed; do not reuse it as unseen evidence for later changes.",
            "Random-case historical evaluation does not establish temporal, employer-group or external generalization.",
            "The source dataset was explored historically before this reconstruction.",
            "Intervals condition on fixed models and class counts; they exclude training and selection uncertainty.",
            "Segment results are descriptive, overlap and have no multiple-comparison correction.",
            "Calibration was assessed, not fitted; probability quality is not validated for individual decisions.",
            "Competition metric variant and leaderboard placement remain unverified.",
            "This study is not validated for determining visa eligibility or automating immigration decisions.",
        ],
    )
    output_dir.mkdir(parents=True, exist_ok=False)
    np.savez_compressed(output_dir / "holdout_predictions.npz",
                        labels=partitions.holdout[TARGET].to_numpy(), **probabilities)
    (output_dir / "metrics.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    write_plot(report, output_dir / "evaluation.png")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/raw")
    parser.add_argument("--selection-dir", type=Path, default=ROOT / "reports/generated/selection")
    parser.add_argument("--baseline-dir", type=Path, default=ROOT / "reports/generated/baseline")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports/generated/evaluation")
    args = parser.parse_args()
    report = run(args.data_dir, args.selection_dir, args.baseline_dir, args.output_dir)
    print(json.dumps({key: report[key] for key in (
        "rows", "class_counts", "metrics", "uncertainty", "delta_f1_selected_minus_logistic",
    )}, indent=2))


if __name__ == "__main__":
    main()