"""Inference contracts with artificial inputs; no competition files required."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import joblib
import numpy as np

from scripts.inspect_data import FEATURES, IDENTIFIER, TARGET
from test_baseline import fixture
from topvistos.data import sha256_file
from topvistos.selection import build_candidate
from topvistos.predict import ROOT, load_bundle, predict_frame, read_input, run, validate_input


class InferenceTests(unittest.TestCase):
    def test_uses_probabilities_and_exact_threshold_preserving_id_order(self):
        frame = fixture(3).drop(columns=TARGET)
        frame[IDENTIFIER] = ["z", "NA", "a"]
        model = Mock()
        model.predict.side_effect = AssertionError("Do not use the estimator default threshold")
        model.fit.side_effect = AssertionError("Inference must not fit")
        model.predict_proba.return_value = np.array([[0.41, 0.59], [0.4, 0.6], [0.39, 0.61]])
        result = predict_frame(frame, model, 0.6, "recorded")
        self.assertEqual(result[IDENTIFIER].tolist(), ["z", "NA", "a"])
        self.assertEqual(result["predicted_status"].tolist(), ["Negado", "Aprovado", "Aprovado"])
        self.assertEqual(list(model.predict_proba.call_args.args[0].columns), FEATURES)

    def test_rejects_target_duplicate_ids_blank_ids_and_invalid_numbers(self):
        frame = fixture(3).drop(columns=TARGET)
        variants = [fixture(3), frame.assign(id_do_caso=["a", "a", "b"]),
                    frame.assign(id_do_caso=["", "a", "b"]),
                    frame.assign(salario_prevalecente=np.inf),
                    frame.assign(num_de_empregados="invalid")]
        for invalid in variants:
            with self.subTest(columns=list(invalid.columns)), self.assertRaises(ValueError):
                validate_input(invalid)

    def test_csv_preserves_na_id_and_accepts_missing_features(self):
        frame = fixture(3).drop(columns=TARGET)
        frame.loc[0, IDENTIFIER] = "NA"
        frame.loc[0, "salario_prevalecente"] = np.nan
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.csv"
            frame.to_csv(path, index=False)
            result = read_input(path)
        self.assertEqual(result.loc[0, IDENTIFIER], "NA")
        self.assertTrue(np.isnan(result.loc[0, "salario_prevalecente"]))

    def test_rejects_duplicate_csv_header_and_malformed_row(self):
        source = (ROOT / "examples/synthetic_cases.csv").read_text(encoding="utf-8")
        invalids = [source.replace("continente", IDENTIFIER, 1), source + "too,few,columns\n"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.csv"
            for text in invalids:
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(ValueError):
                    read_input(path)

    def test_mismatched_model_or_changed_threshold_fails_before_loading(self):
        decision = json.loads((ROOT / "docs/selection/decision.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            model_path, manifest = Path(directory) / "model.joblib", Path(directory) / "decision.json"
            model_path.write_bytes(b"not a model")
            manifest.write_text(json.dumps(decision), encoding="utf-8")
            with patch("topvistos.predict.joblib.load") as loader:
                with self.assertRaisesRegex(ValueError, "Model hash"):
                    load_bundle(model_path, manifest)
                changed = copy.deepcopy(decision)
                changed["threshold"] = 0.5
                manifest.write_text(json.dumps(changed), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "threshold"):
                    load_bundle(model_path, manifest)
                loader.assert_not_called()

    def test_rebuilt_bundle_is_labelled_and_missing_unseen_inputs_work(self):
        train = fixture()
        spec = json.loads((ROOT / "docs/selection/decision.json").read_text(encoding="utf-8"))["specification"]
        from threadpoolctl import threadpool_limits
        with threadpool_limits(limits=1):
            model = build_candidate(spec).fit(train[FEATURES], train[TARGET])
        decision = json.loads((ROOT / "docs/selection/decision.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            model_path, manifest = folder / "model.joblib", folder / "decision.json"
            joblib.dump(model, model_path)
            decision["model_sha256"] = sha256_file(model_path)
            manifest.write_text(json.dumps(decision), encoding="utf-8")
            summary = run(ROOT / "examples/synthetic_cases.csv", model_path, manifest, folder / "predictions.csv")
            self.assertEqual(summary["artifact_origin"], "rebuilt")
            self.assertEqual(summary["rows"], 3)
            self.assertEqual(summary["threshold"], 0.6)

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "existing.csv"
            path.write_text("keep me", encoding="utf-8")
            with patch("topvistos.predict.load_bundle") as loader, self.assertRaises(FileExistsError):
                run(path, path, path, path)
            self.assertEqual(path.read_text(encoding="utf-8"), "keep me")
            loader.assert_not_called()

    def test_cli_checks_public_example_without_model(self):
        result = subprocess.run(
            [sys.executable, "-m", "topvistos.predict", "--input", "examples/synthetic_cases.csv", "--check-input"],
            cwd=ROOT, text=True, capture_output=True, check=True,
        )
        output = json.loads(result.stdout)
        self.assertEqual(output["rows"], 3)
        self.assertFalse(output["prediction_performed"])

    def test_invalid_probability_distribution_is_rejected(self):
        model = Mock()
        for values in ([[0.2, 0.9]] * 3, [[0.1, np.nan]] * 3, [[1.1, -0.1]] * 3):
            model.predict_proba.return_value = np.array(values)
            with self.assertRaises(ValueError):
                predict_frame(fixture(3).drop(columns=TARGET), model, 0.6, "recorded")


if __name__ == "__main__":
    unittest.main()