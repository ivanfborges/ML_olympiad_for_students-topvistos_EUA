"""Inspect locally supplied competition CSVs without publishing individual rows."""

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path


FEATURES = [
    "continente", "educacao_do_empregado", "tem_experiencia_de_trabalho",
    "requer_treinamento_de_trabalho", "num_de_empregados",
    "ano_de_estabelecimento", "regiao_de_emprego", "salario_prevalecente",
    "unidade_de_salario", "posicao_em_tempo_integral",
]
IDENTIFIER = "id_do_caso"
TARGET = "status_do_caso"
SCHEMAS = {
    "train.csv": [IDENTIFIER, *FEATURES, TARGET],
    "test.csv": [IDENTIFIER, *FEATURES],
    "sample_submission.csv": [IDENTIFIER, TARGET],
}


def inspect_data(data_dir):
    """Validate file structure and return aggregate metadata, never raw records."""
    report = {
        "scope": "Structural data validation; no model training or evaluation.",
        "files": {},
        "warnings": [],
    }
    ids_by_file = {}
    for name, expected_columns in SCHEMAS.items():
        path = Path(data_dir) / name
        raw = path.read_bytes()
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != expected_columns:
                raise ValueError(f"{name}: unexpected columns or column order.")
            rows = list(reader)
        if not rows:
            raise ValueError(f"{name}: no data rows.")
        if any(None in row or any(value is None for value in row.values()) for row in rows):
            raise ValueError(f"{name}: malformed CSV row.")
        ids = [row[IDENTIFIER].strip() for row in rows]
        if any(not value for value in ids):
            raise ValueError(f"{name}: blank case identifier.")
        if len(ids) != len(set(ids)):
            raise ValueError(f"{name}: duplicate case identifiers.")
        targets = Counter(row[TARGET] for row in rows) if TARGET in expected_columns else {}
        if name == "train.csv" and set(targets) != {"Aprovado", "Negado"}:
            raise ValueError("train.csv: expected both original target labels.")
        if name == "sample_submission.csv" and not set(targets).issubset({"0", "1"}):
            raise ValueError("sample_submission.csv: expected binary output labels.")
        report["files"][name] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "rows": len(rows),
            "columns": expected_columns,
            "duplicate_ids": 0,
            "blank_ids": 0,
            "blank_cells": sum(not value.strip() for row in rows for value in row.values()),
            "target_counts": dict(sorted(targets.items())),
        }
        ids_by_file[name] = set(ids)

    overlap = ids_by_file["train.csv"] & ids_by_file["test.csv"]
    if overlap:
        raise ValueError("Training and competition-test case identifiers overlap.")
    sample_ids = ids_by_file["sample_submission.csv"]
    test_ids = ids_by_file["test.csv"]
    matches = sample_ids == test_ids
    report["relationships"] = {
        "train_test_id_overlap": 0,
        "sample_ids_in_test": len(sample_ids & test_ids),
        "sample_ids_outside_test": len(sample_ids - test_ids),
        "sample_covers_full_test_id_set": matches,
    }
    if not matches:
        report["warnings"].append(
            "The supplied sample submission is not the full test-ID template. "
            "Use it only as a format example; generate future predictions from test.csv IDs."
        )
    report["limitations"] = [
        "Matching historical row counts does not independently establish dataset provenance.",
        "Checks cover schema, target encoding, and identifiers, not numeric validity or model leakage.",
        "Competition scoring configuration and data reuse terms have not been independently verified.",
    ]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir", type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "raw",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = inspect_data(args.data_dir)
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"Data validation failed: {error}\n")
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()