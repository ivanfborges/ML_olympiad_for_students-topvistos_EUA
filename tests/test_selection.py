"""Behavioral tests for bounded selection and frozen decision artifacts."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import joblib
import numpy as np
from threadpoolctl import threadpool_limits

from test_baseline import fixture
from scripts.inspect_data import FEATURES, IDENTIFIER, TARGET
from topvistos.data import Partitions, partition_fingerprint, sha256_file, split_labeled
from topvistos.selection import (
    ROOT, build_candidate, check_partitions, choose_candidate, run, score_at_half, select_threshold,
)


def membership(parts):
    return {name: {"rows": len(getattr(parts, name)),
                   "membership_sha256": partition_fingerprint(getattr(parts, name))}
            for name in ("train", "validation", "holdout")}


class SelectionTests(unittest.TestCase):
    def test_cv_uses_explicit_approval_rule_at_exact_half(self):
        from sklearn.dummy import DummyClassifier
        model = DummyClassifier(strategy="prior").fit([[0], [1]], [0, 1])
        result = score_at_half(model, [[0], [1], [2]], [0, 1, 1])
        self.assertAlmostEqual(result["f1_macro"], 0.4)

    def test_candidate_selection_uses_cv_not_validation_and_has_stable_ties(self):
        def candidate(name, cv, validation):
            return {"id": name, "training_cv": {"f1_macro": {"mean": cv}},
                    "validation": {"f1_macro": validation}}
        results = [candidate("first", 0.6, 0.99), candidate("second", 0.7, 0.4),
                   candidate("third", 0.7 + 1e-13, 0.9)]
        self.assertEqual(choose_candidate(results), "second")
        with self.assertRaises(ValueError):
            choose_candidate([candidate("invalid", float("nan"), 1)])

    def test_threshold_ties_prefer_nearest_half_then_lower(self):
        labels, probabilities = [0, 1], [0.1, 0.9]
        chosen, _ = select_threshold(labels, probabilities, [0.8, 0.5, 0.2])
        self.assertEqual(chosen["threshold"], 0.5)
        chosen, _ = select_threshold(labels, probabilities, [0.6, 0.4])
        self.assertEqual(chosen["threshold"], 0.4)

    def test_threshold_boundary_and_class_tradeoff(self):
        probabilities = np.array([0.2, 0.4, 0.6, 0.8])
        before = probabilities.copy()
        _, curve = select_threshold([0, 1, 0, 1], probabilities, [0.2, 0.4, 0.6, 0.8])
        self.assertEqual(curve[0]["confusion_matrix"], [[0, 2], [0, 2]])
        self.assertEqual(curve[1]["confusion_matrix"], [[1, 1], [0, 2]])
        self.assertEqual(curve[-1]["confusion_matrix"], [[2, 0], [1, 1]])
        self.assertEqual(sorted(p["recall_denied"] for p in curve),
                         [p["recall_denied"] for p in curve])
        self.assertEqual(sorted((p["recall_approved"] for p in curve), reverse=True),
                         [p["recall_approved"] for p in curve])
        self.assertEqual(len({p["roc_auc"] for p in curve}), 1)
        np.testing.assert_array_equal(before, probabilities)

    def test_invalid_threshold_grids_are_rejected(self):
        for grid in ([], [float("nan")], [-0.1], [1.1], [0.5, 0.5], [[0.5]]):
            with self.subTest(grid=grid), self.assertRaises(ValueError):
                select_threshold([0, 1], [0.1, 0.9], grid)

    def test_partition_check_rejects_changed_ids_without_needing_holdout_labels(self):
        parts = split_labeled(fixture())
        reference = {"partitions": membership(parts)}
        restricted = Partitions(parts.train, parts.validation, parts.holdout[[IDENTIFIER]].copy())
        self.assertEqual(check_partitions(restricted, reference), reference["partitions"])
        restricted.holdout.loc[0, IDENTIFIER] = "changed-case"
        with self.assertRaisesRegex(ValueError, "membership differs"):
            check_partitions(restricted, reference)

    def test_tree_pipelines_reuse_fitted_preprocessing_for_unseen_missing_inputs(self):
        config = json.loads((ROOT / "configs/selection.json").read_text(encoding="utf-8"))
        data = fixture()
        incoming = data[FEATURES].iloc[:2].copy()
        incoming.loc[0, "continente"] = "new-category"
        incoming.loc[1, "salario_prevalecente"] = np.nan
        incoming.loc[0, "num_de_empregados"] = -5
        for family in ("random_forest", "hist_gradient_boosting"):
            spec = next(item for item in config["candidates"] if item["family"] == family)
            with self.subTest(family=family), threadpool_limits(limits=1):
                model = build_candidate(spec).fit(data[FEATURES], data[TARGET])
                pre = model.named_steps["preprocess"]
                encoder = pre.named_transformers_["categorical"].named_steps["encode"]
                with tempfile.TemporaryDirectory() as directory:
                    model_path = Path(directory) / "model.joblib"
                    joblib.dump(model, model_path)
                    probabilities = joblib.load(model_path).predict_proba(incoming)
                self.assertTrue(np.isfinite(probabilities).all())
                self.assertNotIn("new-category", encoder.categories_[0])

    def test_selection_workflow_freezes_decision_without_holdout_features_or_labels(self):
        data = fixture()
        parts = split_labeled(data)
        restricted = Partitions(parts.train, parts.validation, parts.holdout[[IDENTIFIER]].copy())
        expected = membership(parts)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with patch("topvistos.selection.load_labeled", return_value=data), patch(
                "topvistos.selection.split_labeled", return_value=restricted
            ), patch(
                "topvistos.selection.check_partitions",
                side_effect=lambda actual, _: check_partitions(actual, {"partitions": expected}),
            ), patch("topvistos.selection.write_plot"):
                report = run(Path(directory), output)
            self.assertFalse(report["holdout_evaluated"])
            self.assertEqual(len(report["candidates"]), 7)
            self.assertEqual(report["partitions"], expected)
            decision = json.loads((output / "decision.json").read_text(encoding="utf-8"))
            self.assertFalse(decision["refit_on_validation"])
            self.assertEqual(decision["threshold"], report["selected_threshold"])
            self.assertEqual(decision["model_sha256"], sha256_file(output / "selected_pipeline.joblib"))
            self.assertEqual(report["selected_id"], choose_candidate(report["candidates"]))
            self.assertAlmostEqual(report["validation_selected"]["f1_macro"],
                                   max(p["f1_macro"] for p in report["threshold_curve"]))


if __name__ == "__main__":
    unittest.main()