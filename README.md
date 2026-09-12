# TopVistos EUA — Visa Outcome Classification

**English** | [Português](README.pt-BR.md)

A reproducible classification study built from the 2023 **ML Olympiad for Students — TopVistos EUA** Kaggle project. The current implementation separates training, validation, and a reserved final holdout, fits preprocessing inside each training fold, and compares fixed baselines.

## Results so far

On **3,567 validation cases**, logistic regression achieves **0.681 macro F1** and **0.769 ROC-AUC**, compared with 0.401 and 0.500 for a class-prior baseline. These are development results; the final holdout has not been evaluated.

| Validation metric | Prior baseline | Logistic regression |
|---|---:|---:|
| Macro F1 | 0.401 | 0.681 |
| F1 — approved class | 0.802 | 0.824 |
| ROC-AUC | 0.500 | 0.769 |
| Recall — denied class | 0.000 | 0.448 |

The prior baseline predicts approval for every case. Its approved-class F1 of 0.802 shows why that metric alone gives an incomplete picture. Logistic regression still misses 651 of 1,180 denied cases at the fixed 0.5 threshold.

![Validation comparison of fixed baselines](docs/baseline/validation-baselines.png)

Read the [experiment report](docs/BASELINE.md) for the protocol, cross-validation results, confusion matrix, and limitations. [Machine-readable results](docs/baseline/metrics.json) include data, source, and partition hashes.

## Reproduce the experiment

Use a **stable Python 3.11** release. The recorded run used Python 3.11.14 on Windows. Dependencies are pinned in [requirements-lock.txt](requirements-lock.txt). Run these commands from the repository root.

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-lock.txt
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe -m topvistos.baseline
```

Linux/macOS:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m topvistos.baseline
```

Obtain the [required data](data/README.md) and place it in `data/raw/` before running the experiment. The baseline requires the recorded `train.csv` hash. The tests use synthetic fixtures and run without competition data. Continuous integration installs the locked dependencies and runs the tests on Linux.

Outputs go to `reports/generated/baseline/`: metrics, a chart, partition identifiers, and fitted pipelines. This directory is ignored by Git; only aggregate results and the chart are curated into the documentation. Load serialized models only from a source you trust.

## Engineering choices

- A deterministic, stratified 60/20/20 split; five-fold cross-validation uses only the training partition.
- Imputation, scaling, and category encoding are fitted inside the pipeline; inference handles missing values and unseen categories.
- IDs and the target are excluded from features. Negative employee counts become missing values with an indicator.
- Precision and recall use the correct argument order; ROC-AUC uses probabilities.
- Tests cover data integrity, split separation, preprocessing isolation, metrics, serialization, and execution without final-holdout features or labels.

## Scope and next steps

This study models the historical label `status_do_caso`: `Aprovado=1`, `Negado=0`. It is not validated for visa eligibility or automated immigration decisions. Macro F1 is an internal development criterion; the official competition F1 variant and leaderboard result remain unverified.

Next: compare a small number of candidate models, select any threshold on development data, then evaluate the reserved holdout and errors across relevant segments. The original dataset was explored in the historical notebook, so the reserved partition is not new external evidence. Current scores are not directly comparable with that notebook's different split.

## Historical work and data source

- [Original notebook (Portuguese)](ml-olympiad_top-vistos-eua_solucao.ipynb), preserved unchanged.
- [Reproducibility audit](docs/REPRODUCIBILITY.md).
- [Aggregate data manifest](docs/data-manifest.json).
- [Original competition description (Portuguese)](docs/competition-description.pt-BR.md).

André Lopes. *ML Olympiad for Students — TopVistos EUA* (2023), [Kaggle](https://www.kaggle.com/competitions/ml-olympiad-for-students-topvistos-eua). The author supplied local files matching the historical row counts; original download provenance has not been independently verified. Raw data is not redistributed.