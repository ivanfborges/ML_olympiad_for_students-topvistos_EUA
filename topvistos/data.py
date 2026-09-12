"""Validated labeled inputs and deterministic partitions for the baseline."""

from dataclasses import dataclass
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from scripts.inspect_data import FEATURES, IDENTIFIER, TARGET


@dataclass(frozen=True)
class Partitions:
    train: pd.DataFrame
    validation: pd.DataFrame
    holdout: pd.DataFrame


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_labeled(path, expected_sha256):
    """Require the recorded data version before constructing any partitions."""
    if sha256_file(path) != expected_sha256:
        raise ValueError("train.csv hash differs from the recorded data manifest.")
    frame = pd.read_csv(path, encoding="utf-8-sig", dtype={IDENTIFIER: str})
    expected = [IDENTIFIER, *FEATURES, TARGET]
    if list(frame.columns) != expected:
        raise ValueError("Unexpected labeled-data schema.")
    if frame.empty or frame[IDENTIFIER].isna().any():
        raise ValueError("Labeled data must contain nonempty case identifiers.")
    frame[IDENTIFIER] = frame[IDENTIFIER].str.strip()
    if frame[IDENTIFIER].eq("").any() or frame[IDENTIFIER].duplicated().any():
        raise ValueError("Case identifiers must be unique and nonblank.")
    if set(frame[TARGET].unique()) != {"Aprovado", "Negado"}:
        raise ValueError("Expected original Aprovado/Negado labels.")
    frame[TARGET] = frame[TARGET].map({"Negado": 0, "Aprovado": 1}).astype(int)
    # Row order in an input CSV must not silently redefine the split.
    return frame.sort_values(IDENTIFIER).reset_index(drop=True)


def split_labeled(frame, seed=42):
    """60/20/20 stratified case split; holdout is reserved for a later stage."""
    if len(frame) < 30 or frame[TARGET].value_counts().min() < 10:
        raise ValueError("Insufficient labeled cases for stratified partitions.")
    ordered = frame.sort_values(IDENTIFIER).reset_index(drop=True)
    development, holdout = train_test_split(
        ordered, test_size=0.20, stratify=ordered[TARGET], random_state=seed
    )
    train, validation = train_test_split(
        development, test_size=0.25,
        stratify=development[TARGET], random_state=seed,
    )
    result = Partitions(
        train=train.reset_index(drop=True),
        validation=validation.reset_index(drop=True),
        holdout=holdout.reset_index(drop=True),
    )
    sets = [set(part[IDENTIFIER]) for part in (result.train, result.validation, result.holdout)]
    if any(sets[i] & sets[j] for i in range(3) for j in range(i + 1, 3)):
        raise ValueError("Partition identifiers overlap.")
    return result


def partition_fingerprint(frame):
    """Public checksum of membership, without publishing case identifiers."""
    ids = sorted(frame[IDENTIFIER].tolist())
    return hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()


def training_quality(frame):
    """Describe predefined quality concerns using training rows only."""
    count = pd.to_numeric(frame["num_de_empregados"], errors="raise")
    return {
        "scope": "training partition only",
        "negative_employee_counts": int((count < 0).sum()),
        "missing_feature_cells": int(frame[FEATURES].isna().sum().sum()),
    }