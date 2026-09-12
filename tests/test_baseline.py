"""Behavioral checks for split boundaries, preprocessing, metrics, and artifacts."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import joblib
import numpy as np
import pandas as pd

from scripts.inspect_data import FEATURES, IDENTIFIER, TARGET
from topvistos.data import Partitions, load_labeled, sha256_file, split_labeled
from topvistos.modeling import (
    CATEGORICAL, build_logistic, classification_metrics, normalize_features,
)
from topvistos.baseline import run


def fixture(rows=120):
    index = np.arange(rows)
    data = {name: ["example"] * rows for name in CATEGORICAL}
    data.update({
        "num_de_empregados": (index + 10).astype(float),
        "ano_de_estabelecimento": (1980 + index % 30).astype(float),
        "salario_prevalecente": (1000 + index * 17).astype(float),
        IDENTIFIER: [f"case-{i:04d}" for i in index],
        TARGET: (index % 3 != 0).astype(int),
    })
    return pd.DataFrame(data).loc[:, [IDENTIFIER, *FEATURES, TARGET]]


class SplitAndInputTests(unittest.TestCase):
    def test_partition_membership_is_complete_disjoint_and_order_independent(self):
        data = fixture()
        original = split_labeled(data)
        shuffled = split_labeled(data.sample(frac=1, random_state=7))
        memberships = []
        for name in ("train", "validation", "holdout"):
            part = getattr(original, name)
            ids = set(part[IDENTIFIER])
            self.assertEqual(ids, set(getattr(shuffled, name)[IDENTIFIER]))
            self.assertEqual(set(part[TARGET]), {0, 1})
            memberships.append(ids)
        self.assertEqual(set.union(*memberships), set(data[IDENTIFIER]))
        self.assertFalse(memberships[0] & memberships[1])
        self.assertFalse(memberships[0] & memberships[2])
        self.assertFalse(memberships[1] & memberships[2])
        self.assertEqual([len(x) for x in memberships], [72, 24, 24])

    def test_data_hash_change_fails_before_loading(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "train.csv"
            path.write_text("changed input", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash differs"):
                load_labeled(path, "0" * 64)

    def test_original_labels_are_encoded_and_duplicate_ids_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "train.csv"
            data = fixture()
            data[TARGET] = data[TARGET].map({0: "Negado", 1: "Aprovado"})
            data.to_csv(path, index=False)
            encoded = load_labeled(path, sha256_file(path))
            self.assertEqual(set(encoded[TARGET]), {0, 1})
            data.loc[1, IDENTIFIER] = data.loc[0, IDENTIFIER]
            data.to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "unique"):
                load_labeled(path, sha256_file(path))


class PreprocessingAndMetricsTests(unittest.TestCase):
    def test_learned_statistics_and_categories_do_not_change_at_inference(self):
        data = fixture(30)
        data["num_de_empregados"] = 20.0
        data.loc[0, "num_de_empregados"] = -1.0
        pipeline = build_logistic().fit(data[FEATURES], data[TARGET])
        preprocessing = pipeline.named_steps["preprocess"]
        imputer = preprocessing.named_transformers_["numeric"].named_steps["imputer"]
        encoder = preprocessing.named_transformers_["categorical"].named_steps["encode"]
        before = imputer.statistics_.copy()
        self.assertEqual(before[0], 20.0)
        unseen = data[FEATURES].iloc[:1].copy()
        unseen["continente"] = "unseen-category"
        unseen["num_de_empregados"] = 1_000_000.0
        probabilities = pipeline.predict_proba(unseen)
        np.testing.assert_array_equal(before, imputer.statistics_)
        self.assertNotIn("unseen-category", encoder.categories_[0])
        self.assertTrue(np.isfinite(probabilities).all())

    def test_unknown_and_missing_inputs_survive_serialization(self):
        data = fixture(30)
        pipeline = build_logistic().fit(data[FEATURES], data[TARGET])
        incoming = data[FEATURES].iloc[:2].copy()
        incoming.loc[incoming.index[0], "continente"] = "unseen-category"
        incoming.loc[incoming.index[1], "salario_prevalecente"] = np.nan
        incoming.loc[incoming.index[0], "num_de_empregados"] = -3
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.joblib"
            joblib.dump(pipeline, path)
            restored = joblib.load(path)
            np.testing.assert_array_equal(
                pipeline.predict_proba(incoming), restored.predict_proba(incoming)
            )

    def test_target_ids_and_infinite_values_are_rejected_as_features(self):
        data = fixture(30)
        with self.assertRaisesRegex(ValueError, "exclude IDs and target"):
            normalize_features(data)
        incoming = data[FEATURES].copy()
        incoming.loc[0, "salario_prevalecente"] = np.inf
        with self.assertRaisesRegex(ValueError, "infinite"):
            normalize_features(incoming)

    def test_negative_employee_count_is_missing_and_flagged_without_mutating_input(self):
        incoming = fixture(30)[FEATURES]
        incoming.loc[0, "num_de_empregados"] = -2
        result = normalize_features(incoming)
        self.assertTrue(np.isnan(result.loc[0, "num_de_empregados"]))
        self.assertEqual(result.loc[0, "employee_count_invalid"], 1.0)
        self.assertEqual(incoming.loc[0, "num_de_empregados"], -2)

    def test_precision_recall_order_and_probability_auc(self):
        result = classification_metrics([0, 0, 0, 1], [0.1, 0.2, 0.8, 0.9])
        self.assertEqual(result["precision_approved"], 0.5)
        self.assertEqual(result["recall_approved"], 1.0)
        self.assertEqual(result["roc_auc"], 1.0)
        self.assertEqual(result["confusion_matrix"], [[2, 1], [0, 1]])

    def test_invalid_probability_vectors_are_rejected(self):
        for probabilities in ([0.1], [0.1, np.nan], [-1, 0.9], [0.1, 1.1]):
            with self.subTest(probabilities=probabilities), self.assertRaises(ValueError):
                classification_metrics([0, 1], probabilities)


class WorkflowBoundaryTests(unittest.TestCase):
    def test_entire_workflow_runs_with_no_holdout_features_or_labels(self):
        data = fixture()
        parts = split_labeled(data)
        restricted = Partitions(
            parts.train, parts.validation, parts.holdout[[IDENTIFIER]].copy()
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            with patch("topvistos.baseline.load_labeled", return_value=data), patch(
                "topvistos.baseline.split_labeled", return_value=restricted
            ), patch("topvistos.baseline.write_plot"):
                report = run(Path(directory), output)
            self.assertFalse(report["holdout_evaluated"])
            self.assertEqual(report["partitions"]["holdout"]["rows"], 24)
            self.assertEqual(set(report["results"]), {"prior_baseline", "logistic_regression"})
            saved = json.loads((output / "metrics.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["results"], report["results"])


if __name__ == "__main__":
    unittest.main()