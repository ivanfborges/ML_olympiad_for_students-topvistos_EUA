"""Checks for frozen-artifact gates and final-evaluation statistics."""

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import joblib
import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.pipeline import Pipeline

from scripts.inspect_data import FEATURES, TARGET
from test_baseline import fixture
from topvistos.data import sha256_file, split_labeled
from topvistos.evaluation import ROOT, evaluate_holdout, load_frozen_models, run
from topvistos.evaluation_stats import (
    bootstrap_intervals, calibration_summary, macro_f1, segment_summary, wilson_interval,
)
from topvistos.modeling import build_logistic, classification_metrics


class DiagnosticTests(unittest.TestCase):
    def test_wilson_handles_zero_all_and_empty_counts(self):
        self.assertIsNone(wilson_interval(0, 0))
        low, high = wilson_interval(0, 10)
        self.assertAlmostEqual(low, 0)
        self.assertAlmostEqual(high, 0.2775328, places=6)
        low, high = wilson_interval(10, 10)
        self.assertAlmostEqual(low, 0.7224672, places=6)
        self.assertAlmostEqual(high, 1)
        with self.assertRaises(ValueError):
            wilson_interval(11, 10)

    def test_fast_macro_matches_reference_with_asymmetric_and_constant_predictions(self):
        labels = np.array([0, 0, 1, 1, 1])
        for p in ([0, 1, 0, 1, 1], [1] * 5, [0] * 5):
            expected = classification_metrics(labels, p)["f1_macro"]
            self.assertAlmostEqual(macro_f1(labels, p), expected)

    def test_paired_bootstrap_identical_models_have_exact_zero_difference(self):
        labels = [0, 0, 1, 1, 1]
        p = np.array([0.1, 0.6, 0.4, 0.8, 0.9])
        probabilities = {name: p for name in ("prior_baseline", "logistic_regression", "selected_boosting")}
        thresholds = {name: 0.5 for name in probabilities}
        result = bootstrap_intervals(labels, probabilities, thresholds, resamples=30, seed=5)
        repeated = bootstrap_intervals(labels, probabilities, thresholds, resamples=30, seed=5)
        self.assertEqual(result, repeated)
        self.assertEqual(result["intervals"]["delta_f1_selected_minus_logistic"], [0, 0])

    def test_calibration_bins_cover_zero_one_boundaries_and_empty_bins(self):
        result = calibration_summary([0, 1, 0, 1], [0, 0.1, 0.5, 1], bins=10)
        bins = result["bins"]
        self.assertEqual(sum(item["rows"] for item in bins), 4)
        self.assertEqual([bins[i]["rows"] for i in (0, 1, 5, 9)], [1, 1, 1, 1])
        self.assertIsNone(bins[2]["mean_probability"])
        self.assertIsNone(bins[2]["observed_rate_wilson95"])
        self.assertTrue(bins[9]["upper_inclusive"])
        self.assertAlmostEqual(result["ece"], 0.35)

    def test_segment_support_and_recall_use_correct_class_denominators(self):
        frame = fixture(120)
        frame["continente"] = ["large"] * 100 + ["small"] * 20
        labels = np.array([0] * 40 + [1] * 60 + [0] * 20)
        p = np.array([0.2] * 30 + [0.8] * 10 + [0.2] * 15 + [0.8] * 45 + [0.2] * 20)
        groups = segment_summary(frame, labels, p, 0.6, ["continente"])["groups"]["continente"]
        large, small = groups
        self.assertEqual(large["metrics"]["confusion_matrix"], [[30, 10], [15, 45]])
        self.assertEqual(large["metrics"]["recall_denied"], 0.75)
        self.assertEqual(large["recall_denied_wilson95"], wilson_interval(30, 40))
        self.assertIsNone(small["metrics"])
        self.assertEqual(small["denied"], 20)


class FrozenEvaluationTests(unittest.TestCase):
    def test_changed_threshold_is_rejected_before_model_loading(self):
        config = {"models": {"selected_boosting": {"sha256": "expected", "threshold": 0.6}}}
        decision = {"model_sha256": "expected", "threshold": 0.5}
        with patch("topvistos.evaluation.joblib.load") as loader:
            with self.assertRaisesRegex(ValueError, "frozen model or threshold"):
                load_frozen_models({}, config, decision, {"packages": {}})
            loader.assert_not_called()

    def test_modified_model_bytes_are_rejected_before_deserialization(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.joblib"
            path.write_bytes(b"not a pickle")
            config = {"models": {"selected_boosting": {"sha256": "0" * 64, "threshold": 0.6}}}
            decision = {"model_sha256": "0" * 64, "threshold": 0.6, "refit_on_validation": False,
                        "prediction_rule": "approval_probability >= threshold", "source_sha256": {}}
            with patch("topvistos.evaluation.joblib.load") as loader:
                with self.assertRaisesRegex(ValueError, "model hash mismatch"):
                    load_frozen_models({"selected_boosting": path}, config, decision, {"packages": {}})
                loader.assert_not_called()

    def test_existing_output_fails_before_loading_or_scoring(self):
        with tempfile.TemporaryDirectory() as directory, patch("topvistos.evaluation.load_frozen_models") as loader:
            with self.assertRaises(FileExistsError):
                run(Path(directory), Path(directory), Path(directory), Path(directory))
            loader.assert_not_called()

    def test_evaluation_never_refits_or_changes_model_and_threshold(self):
        data = fixture()
        parts = split_labeled(data)
        X, y = parts.train[FEATURES], parts.train[TARGET]
        models = {
            "prior_baseline": DummyClassifier(strategy="prior").fit(X, y),
            "logistic_regression": build_logistic().fit(X, y),
            "selected_boosting": build_logistic().fit(X, y),
        }
        config = json.loads((ROOT / "configs/evaluation.json").read_text(encoding="utf-8"))
        config["bootstrap"]["resamples"] = 10
        before = copy.deepcopy(config)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "models.joblib"
            joblib.dump(models, path)
            digest = sha256_file(path)
            with patch.object(Pipeline, "fit", side_effect=AssertionError("Evaluation must not fit")):
                report, probabilities = evaluate_holdout(parts.holdout, models, config)
            joblib.dump(models, path)
            self.assertEqual(digest, sha256_file(path))
        self.assertEqual(config, before)
        expected = classification_metrics(parts.holdout[TARGET], probabilities["selected_boosting"], 0.6)
        self.assertEqual(report["metrics"]["selected_boosting"], expected)
        self.assertEqual(report["rows"], 24)


if __name__ == "__main__":
    unittest.main()