"""Tests use tiny artificial CSV fixtures, not the competition records."""

import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location(
    "inspect_data", Path(__file__).resolve().parents[1] / "scripts" / "inspect_data.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DataInspectionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.write("train.csv", [
            ["train-a", *(["value"] * 10), "Aprovado"],
            ["train-b", *(["value"] * 10), "Negado"],
        ])
        self.write("test.csv", [["test-a", *(["value"] * 10)]])
        self.write("sample_submission.csv", [["test-a", "0"]])

    def write(self, name, rows, headers=None):
        with (self.root / name).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(headers if headers is not None else MODULE.SCHEMAS[name])
            writer.writerows(rows)

    def test_complete_template_has_no_warning_or_raw_ids_in_report(self):
        report = MODULE.inspect_data(self.root)
        self.assertTrue(report["relationships"]["sample_covers_full_test_id_set"])
        self.assertEqual(report["warnings"], [])
        self.assertNotIn("train-a", str(report))
        self.assertEqual(report["files"]["train.csv"]["rows"], 2)

    def test_partial_or_unrelated_template_is_a_warning(self):
        self.write("sample_submission.csv", [["example-only", "1"]])
        report = MODULE.inspect_data(self.root)
        self.assertFalse(report["relationships"]["sample_covers_full_test_id_set"])
        self.assertEqual(report["relationships"]["sample_ids_outside_test"], 1)
        self.assertTrue(report["warnings"])

    def test_overlap_between_train_and_test_is_rejected(self):
        self.write("test.csv", [["train-a", *(["value"] * 10)]])
        with self.assertRaisesRegex(ValueError, "overlap"):
            MODULE.inspect_data(self.root)

    def test_duplicate_ids_are_rejected(self):
        self.write("test.csv", [["test-a", *(["value"] * 10)]] * 2)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            MODULE.inspect_data(self.root)

    def test_target_is_not_allowed_in_unlabeled_test_file(self):
        self.write("test.csv", [["test-a", *(["value"] * 10), "Aprovado"]],
                   headers=MODULE.SCHEMAS["train.csv"])
        with self.assertRaisesRegex(ValueError, "columns"):
            MODULE.inspect_data(self.root)

    def test_incorrect_target_encoding_is_rejected(self):
        self.write("train.csv", [
            ["train-a", *(["value"] * 10), "1"],
            ["train-b", *(["value"] * 10), "0"],
        ])
        with self.assertRaisesRegex(ValueError, "target labels"):
            MODULE.inspect_data(self.root)

    def test_malformed_rows_are_rejected(self):
        self.write("test.csv", [["test-a", "too-few-fields"]])
        with self.assertRaisesRegex(ValueError, "malformed"):
            MODULE.inspect_data(self.root)


if __name__ == "__main__":
    unittest.main()